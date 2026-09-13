"""Adaptador HTTP del módulo Usuario."""

from __future__ import annotations

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.app.modules.usuario.adapters.outbound.provider import (
    password_hasher as _password_hasher,
    repository as _repository,
    telegram_link_repository as _telegram_link_repository,
    token_service as _token_service,
)
from backend.app.modules.usuario.application.use_cases.get_current_user import GetCurrentUserUseCase
from backend.app.modules.usuario.application.use_cases.link_telegram import (
    ConfirmTelegramLinkUseCase,
    CreateTelegramLinkUseCase,
    TelegramAlreadyLinkedError,
    TelegramLinkTokenInvalidError,
    UserAlreadyLinkedError,
)
from backend.app.modules.usuario.application.use_cases.login_user import (
    InactiveUserError,
    InvalidCredentialsError,
    LoginUserUseCase,
)
from backend.app.modules.usuario.application.use_cases.register_user import (
    RegisterUserUseCase,
    UserAlreadyExistsError,
)
from backend.app.modules.usuario.domain.entities.usuario import Usuario
from backend.app.modules.usuario.domain.value_objects.email import InvalidEmailError

router = APIRouter(prefix="/users", tags=["users"])

_bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)]


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    status: str
    telegram_linked: bool

    @classmethod
    def from_domain(cls, user: Usuario) -> "UserResponse":
        return cls(
            id=user.id,
            name=user.name,
            email=str(user.email),
            status=user.status.value,
            telegram_linked=user.telegram_user_id is not None,
        )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TelegramLinkResponse(BaseModel):
    telegram_deep_link: str
    expires_at: str


class TelegramLinkConfirmRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=64)
    telegram_user_id: int = Field(..., gt=0)


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
            name=payload.name,
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
    },
)
def login_user(payload: UserLoginRequest) -> LoginResponse:
    use_case = LoginUserUseCase(_repository, _password_hasher, _token_service)
    try:
        access_token = use_case.execute(
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
    except InvalidEmailError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return LoginResponse(access_token=access_token)


@router.get(
    "/me",
    responses={401: {"model": ErrorResponse, "description": "Credenciales ausentes, inválidas o expiradas."}},
)
def get_current_user(credentials: BearerCredentials) -> UserResponse:
    """Devuelve el perfil del usuario autenticado mediante Bearer JWT."""
    return UserResponse.from_domain(_authenticated_user(credentials))


def _authenticated_user(credentials: HTTPAuthorizationCredentials | None) -> Usuario:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación requeridas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = _token_service.verify_access_token(credentials.credentials)
        return GetCurrentUserUseCase(_repository).execute(user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o usuario no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


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


@router.post(
    "/telegram/link/confirm",
    responses={
        400: {"model": ErrorResponse, "description": "El token de vinculación es inválido o expiró."},
        409: {"model": ErrorResponse, "description": "La cuenta ya está vinculada con Telegram."},
        422: {"model": ErrorResponse, "description": "Los datos del usuario no son válidos."},
    },
)
def confirm_telegram_link(payload: TelegramLinkConfirmRequest) -> UserResponse:
    """Confirma una vinculación usando la identidad recibida por el bot de Telegram.

    Este endpoint representa el callback interno del bot: telegram_user_id debe
    provenir del usuario que inició el bot mediante el deep link.
    """
    try:
        user = ConfirmTelegramLinkUseCase(_repository, _telegram_link_repository).execute(
            token=payload.token,
            telegram_user_id=payload.telegram_user_id,
        )
    except TelegramLinkTokenInvalidError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except TelegramAlreadyLinkedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except UserAlreadyLinkedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return UserResponse.from_domain(user)
