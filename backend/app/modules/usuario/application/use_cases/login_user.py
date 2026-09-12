"""Caso de uso para autenticar un usuario."""

from __future__ import annotations

from backend.app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher
from backend.app.modules.usuario.application.ports.outbound.token_service import TokenService
from backend.app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from backend.app.modules.usuario.domain.entities.usuario import Usuario, UserStatus
from backend.app.modules.usuario.domain.value_objects.email import Email


class InvalidCredentialsError(ValueError):
    """Se lanza cuando las credenciales no son válidas."""


class InactiveUserError(ValueError):
    """Se lanza cuando el usuario existe pero está inactivo."""


class LoginUserUseCase:
    """Autentica al usuario y emite un token de acceso."""

    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    def execute(self, email: str, password: str) -> str:
        email_value = Email(email)
        user = self._repository.get_by_email(email_value)

        # No distinguimos entre "correo inexistente" y "contraseña incorrecta".
        # Esto evita revelar si una cuenta existe.
        if user is None or not self._password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError("Correo o contraseña incorrectos.")

        if user.status != UserStatus.ACTIVE:
            raise InactiveUserError("El usuario está inactivo.")

        return self._token_service.create_access_token(user)
