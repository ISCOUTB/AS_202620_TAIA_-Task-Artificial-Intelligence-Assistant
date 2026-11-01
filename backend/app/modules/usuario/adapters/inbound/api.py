"""Adaptador HTTP del módulo Usuario."""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.modules.usuario.adapters.outbound.provider import (
    failed_login_attempt_repository as _failed_login_attempt_repository,
    password_hasher as _password_hasher,
    repository as _repository,
    session_repository as _session_repository,
    telegram_link_repository as _telegram_link_repository,
    token_service as _token_service,
)
from app.modules.usuario.application.ports.outbound.token_service import AccessTokenClaims
from app.modules.usuario.application.use_cases.get_current_user import GetCurrentUserUseCase
from app.modules.usuario.application.use_cases.link_telegram import (
    CreateTelegramLinkUseCase,
    UserAlreadyLinkedError,
)
from app.modules.usuario.application.use_cases.login_user import (
    InactiveUserError,
    InvalidCredentialsError,
    LoginUserUseCase,
    TooManyLoginAttemptsError,
)
from app.modules.usuario.application.use_cases.manage_sessions import (
    AuthenticateAccessTokenUseCase,
    InvalidRefreshTokenError,
    LogoutUseCase,
    RefreshSessionUseCase,
)
from app.modules.usuario.application.use_cases.register_user import (
    RegisterUserUseCase,
    UserAlreadyExistsError,
)
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import InvalidEmailError

router = APIRouter(prefix="/users", tags=["users"])

_bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)]


class UserCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    status: str
    telegram_linked: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, user: Usuario) -> "UserResponse":
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=str(user.email),
            status=user.status.value,
            telegram_linked=user.telegram_user_id is not None,
            created_at=user.created_at,
        )


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TelegramLinkResponse(BaseModel):
    telegram_deep_link: str
    expires_at: str


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por el adaptador cuando la petición falla."""

    detail: str


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Ya existe un usuario registrado con ese correo."},
        422: {"model": ErrorResponse, "description": "Los datos del usuario no son válidos."},
    },
)
def register_user(payload: UserCreateRequest) -> UserResponse:
    use_case = RegisterUserUseCase(_repository, _password_hasher)
    try:
        user = use_case.execute(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
        )
    except UserAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return UserResponse.from_domain(user)


@router.post(
    "/login",
    responses={
        401: {"model": ErrorResponse, "description": "Credenciales ausentes, inválidas o expiradas."},
        403: {"model": ErrorResponse, "description": "La cuenta está inactiva."},
        422: {"model": ErrorResponse, "description": "Los datos del usuario no son válidos."},
        429: {"model": ErrorResponse, "description": "Demasiados intentos fallidos con ese correo (RNF-03)."},
    },
)
def login_user(payload: UserLoginRequest) -> LoginResponse:
    use_case = LoginUserUseCase(
        _repository,
        _password_hasher,
        _token_service,
        _failed_login_attempt_repository,
        _session_repository,
    )
    try:
        tokens = use_case.execute(
            email=payload.email,
            password=payload.password,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except InactiveUserError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except TooManyLoginAttemptsError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(error),
        ) from error
    except InvalidEmailError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return LoginResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post(
    "/refresh",
    responses={401: {"model": ErrorResponse, "description": "Token de renovación inválido, expirado o revocado."}},
)
def refresh_session(payload: RefreshTokenRequest) -> LoginResponse:
    """Entrega un par de tokens nuevo; el token de renovación usado deja de servir (RF-USR-03)."""
    use_case = RefreshSessionUseCase(_repository, _session_repository, _token_service)
    try:
        tokens = use_case.execute(payload.refresh_token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return LoginResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse, "description": "Credenciales ausentes, inválidas o expiradas."}},
)
def logout_user(credentials: BearerCredentials) -> Response:
    """Cierra la sesión actual: su token de acceso y su token de renovación dejan de valer (RF-USR-04)."""
    claims = _authenticated_claims(credentials)
    LogoutUseCase(_session_repository).execute(claims.session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    responses={401: {"model": ErrorResponse, "description": "Credenciales ausentes, inválidas o expiradas."}},
)
def get_current_user(credentials: BearerCredentials) -> UserResponse:
    """Devuelve el perfil del usuario autenticado mediante Bearer JWT."""
    return UserResponse.from_domain(_authenticated_user(credentials))


def _authenticated_user(credentials: HTTPAuthorizationCredentials | None) -> Usuario:
    claims = _authenticated_claims(credentials)
    try:
        return GetCurrentUserUseCase(_repository).execute(claims.user_id)
    except ValueError as error:
        raise _invalid_access_token() from error


def _authenticated_claims(credentials: HTTPAuthorizationCredentials | None) -> AccessTokenClaims:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación requeridas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return AuthenticateAccessTokenUseCase(_token_service, _session_repository).execute(
            credentials.credentials
        )
    except ValueError as error:
        raise _invalid_access_token() from error


def _invalid_access_token() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acceso inválido o usuario no encontrado.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/me/telegram/link",
    responses={
        401: {"model": ErrorResponse, "description": "Credenciales ausentes, inválidas o expiradas."},
        409: {"model": ErrorResponse, "description": "La cuenta ya está vinculada con Telegram."},
    },
)
def create_telegram_link(credentials: BearerCredentials) -> TelegramLinkResponse:
    """Genera un enlace temporal para vincular la cuenta Telegram existente del usuario."""
    user = _authenticated_user(credentials)
    try:
        link = CreateTelegramLinkUseCase(_repository, _telegram_link_repository).execute(user.id)
    except UserAlreadyLinkedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    bot_username = os.getenv("TAIA_TELEGRAM_BOT_USERNAME", "taia_bot")
    return TelegramLinkResponse(
        telegram_deep_link=f"https://t.me/{bot_username}?start={link.token}",
        expires_at=link.expires_at.isoformat(),
    )
