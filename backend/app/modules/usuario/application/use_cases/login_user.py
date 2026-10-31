"""Caso de uso para autenticar un usuario."""

from __future__ import annotations

from datetime import timedelta

from app.modules.usuario.application.ports.outbound.failed_login_attempt_repository import (
    FailedLoginAttemptRepository,
)
from app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher
from app.modules.usuario.application.ports.outbound.token_service import TokenService
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.domain.entities.usuario import Usuario, UserStatus
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import Clock, now_bogota


class InvalidCredentialsError(ValueError):
    """Se lanza cuando las credenciales no son válidas."""


class InactiveUserError(ValueError):
    """Se lanza cuando el usuario existe pero está inactivo."""


class TooManyLoginAttemptsError(ValueError):
    """Se lanza cuando el correo superó el límite de intentos fallidos (RNF-03)."""


class LoginUserUseCase:
    """Autentica al usuario y emite un token de acceso."""

    # RNF-03: 5 fallos por identificador cada 15 minutos.
    max_failed_attempts = 5
    attempts_window = timedelta(minutes=15)

    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        failed_attempts: FailedLoginAttemptRepository,
        now: Clock = now_bogota,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._failed_attempts = failed_attempts
        self._now = now

    def execute(self, email: str, password: str) -> str:
        email_value = Email(email)
        now = self._now()

        # Se comprueba antes de verificar la contraseña: con el límite superado,
        # ni la contraseña correcta permite entrar hasta que pase la ventana.
        recent_failures = self._failed_attempts.count_since(
            str(email_value), now - self.attempts_window
        )
        if recent_failures >= self.max_failed_attempts:
            raise TooManyLoginAttemptsError(
                "Demasiados intentos fallidos. Intenta de nuevo en 15 minutos."
            )

        user = self._repository.get_by_email(email_value)

        # No distinguimos entre "correo inexistente" y "contraseña incorrecta".
        # Esto evita revelar si una cuenta existe. Por la misma razón, el límite
        # se aplica también a correos que no están registrados.
        if user is None or not self._password_hasher.verify(password, user.password_hash):
            self._failed_attempts.add(str(email_value), now)
            raise InvalidCredentialsError("Correo o contraseña incorrectos.")

        if user.status is not UserStatus.ACTIVE:
            raise InactiveUserError("El usuario está inactivo.")

        return self._token_service.create_access_token(user)
