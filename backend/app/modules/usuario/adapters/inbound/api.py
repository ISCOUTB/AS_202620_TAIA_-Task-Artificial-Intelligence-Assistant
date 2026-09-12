"""Adaptador HTTP del módulo Usuario."""

from __future__ import annotations

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from backend.app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from backend.app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from backend.app.modules.usuario.adapters.outbound.in_memory_telegram_link_repository import InMemoryTelegramLinkRepository
from backend.app.modules.usuario.application.use_cases.get_current_user import (
    AuthenticatedUserNotFoundError,
    GetCurrentUserUseCase,
)
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
from backend.app.modules.usuario.domain.entities.usuario import InvalidUserError, Usuario
from backend.app.modules.usuario.domain.value_objects.email import InvalidEmailError

router = APIRouter(prefix="/users", tags=["users"])

_repository = InMemoryUserRepository()
_password_hasher = Pbkdf2PasswordHasher()
_token_service = JwtTokenService()
_bearer_scheme = HTTPBearer(auto_error=False)
_telegram_link_repository = InMemoryTelegramLinkRepository()


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


UNAUTHORIZED_RESPONSE = {
    401: {"model": ErrorResponse, "description": "Credenciales ausentes, inválidas o expiradas."}
}
INACTIVE_USER_RESPONSE = {
    403: {"model": ErrorResponse, "description": "La cuenta está inactiva."}
}
USER_ALREADY_EXISTS_RESPONSE = {
    409: {"model": ErrorResponse, "description": "Ya existe un usuario registrado con ese correo."}
}
ALREADY_LINKED_RESPONSE = {
    409: {"model": ErrorResponse, "description": "La cuenta ya está vinculada con Telegram."}
}
INVALID_LINK_TOKEN_RESPONSE = {
    400: {"model": ErrorResponse, "description": "El token de vinculación es inválido o expiró."}
}
INVALID_USER_RESPONSE = {
    422: {"model": ErrorResponse, "description": "Los datos del usuario no son válidos."}
}


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**USER_ALREADY_EXISTS_RESPONSE, **INVALID_USER_RESPONSE},
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
    except (InvalidEmailError, InvalidUserError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return UserResponse.from_domain(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={**UNAUTHORIZED_RESPONSE, **INACTIVE_USER_RESPONSE, **INVALID_USER_RESPONSE},
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
    response_model=UserResponse,
    responses=UNAUTHORIZED_RESPONSE,
)
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> UserResponse:
    """Devuelve el perfil del usuario autenticado mediante Bearer JWT."""
    return UserResponse.from_domain(_authenticated_user(credentials))


def get_authenticated_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> uuid.UUID:
    """Devuelve únicamente el identificador del usuario autenticado.

    Esta dependencia permite que otros contextos consuman la identidad sin
    importar la entidad Usuario ni sus detalles internos.
    """
    return _authenticated_user(credentials).id


def get_user_by_id(user_id: uuid.UUID) -> Usuario | None:
    """Read-only lookup used by other bounded contexts through a small port-like helper."""
    return _repository.get_by_id(user_id)


def get_telegram_user_id(user_id: uuid.UUID) -> int | None:
    """Returns the Telegram chat/user id linked to a TAIA user, if any."""
    user = _repository.get_by_id(user_id)
    return user.telegram_user_id if user is not None else None


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
    except (ValueError, AuthenticatedUserNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o usuario no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


@router.post(
    "/me/telegram/link",
    response_model=TelegramLinkResponse,
    responses={**UNAUTHORIZED_RESPONSE, **ALREADY_LINKED_RESPONSE},
)
def create_telegram_link(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TelegramLinkResponse:
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
    response_model=UserResponse,
    responses={**INVALID_LINK_TOKEN_RESPONSE, **ALREADY_LINKED_RESPONSE, **INVALID_USER_RESPONSE},
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
