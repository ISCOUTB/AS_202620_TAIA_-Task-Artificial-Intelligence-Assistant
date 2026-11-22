"""Recuperar la contraseña con un código de verificación enviado al correo (RF-USR-08, RNF-03)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher
from app.modules.usuario.application.ports.outbound.password_reset_code_repository import (
    PasswordResetCodeRepository,
)
from app.modules.usuario.application.ports.outbound.password_reset_mailer import (
    PasswordResetMailError,
    PasswordResetMailer,
)
from app.modules.usuario.application.ports.outbound.password_reset_request_repository import (
    PasswordResetRequestRepository,
)
from app.modules.usuario.application.ports.outbound.session_repository import SessionRepository
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.application.use_cases.register_user import check_password_rules
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import Clock, now_bogota

logger = logging.getLogger("taia.usuario")

# RF-USR-08: código de 6 dígitos, 15 minutos y 5 intentos fallidos.
CODE_DIGITS = 6
CODE_LIFETIME = timedelta(minutes=15)
MAX_FAILED_ATTEMPTS = 5
# RNF-03: 3 solicitudes por correo en las últimas 24 horas.
MAX_REQUESTS = 3
REQUESTS_WINDOW = timedelta(hours=24)


class TooManyResetRequestsError(ValueError):
    """El correo agotó sus solicitudes de recuperación de las últimas 24 horas (RNF-03)."""


class InvalidResetCodeError(ValueError):
    """Correo inexistente o código incorrecto, vencido, usado o invalidado: no se dice cuál."""


def generate_code() -> str:
    """Código aleatorio de 6 dígitos generado con `secrets`."""
    return f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"


def hash_code(code: str) -> str:
    """El código se guarda solo como SHA-256 (diccionario 5.4)."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class RequestPasswordResetUseCase:
    """Registra la solicitud y, si la cuenta existe, envía un código nuevo (RF-USR-08).

    Antes de responder solo se ejecuta `execute`, que no depende de que la cuenta exista.
    `deliver` se ejecuta después de responder: así el tiempo de respuesta no revela si existe.
    """

    def __init__(
        self,
        users: UserRepository,
        requests: PasswordResetRequestRepository,
        codes: PasswordResetCodeRepository,
        mailer: PasswordResetMailer,
        now: Clock = now_bogota,
    ) -> None:
        self._users = users
        self._requests = requests
        self._codes = codes
        self._mailer = mailer
        self._now = now

    def execute(self, email: str) -> str:
        """Aplica el límite y registra la solicitud. Devuelve el correo normalizado para `deliver`."""
        email_value = Email(email)
        now = self._now()

        # El límite se cuenta para cualquier correo: el 429 no revela si la cuenta existe.
        if self._requests.count_since(str(email_value), now - REQUESTS_WINDOW) >= MAX_REQUESTS:
            raise TooManyResetRequestsError(
                "Agotaste las solicitudes de recuperación de contraseña por hoy. "
                "Intenta de nuevo en 24 horas."
            )
        self._requests.add(str(email_value), now)
        return str(email_value)

    def deliver(self, email: str) -> None:
        """Si la cuenta existe, invalida los códigos anteriores y envía uno nuevo."""
        email_value = Email(email)
        now = self._now()
        user = self._users.get_by_email(email_value)
        if user is None:
            return

        code = generate_code()
        self._codes.replace(user.id, hash_code(code), now, now + CODE_LIFETIME)
        try:
            self._mailer.send_code(str(email_value), code)
        except PasswordResetMailError as error:
            # La respuesta ya fue 202: el error solo queda en el log.
            logger.warning("usuario.password_reset_mail_failed user_id=%s reason=%s", user.id, error)


class ResetPasswordUseCase:
    """Cambia la contraseña con el código vigente y revoca todas las sesiones (RF-USR-08)."""

    def __init__(
        self,
        users: UserRepository,
        codes: PasswordResetCodeRepository,
        hasher: PasswordHasher,
        sessions: SessionRepository,
        now: Clock = now_bogota,
    ) -> None:
        self._users = users
        self._codes = codes
        self._hasher = hasher
        self._sessions = sessions
        self._now = now

    def execute(self, email: str, code: str, new_password: str) -> None:
        check_password_rules(new_password)
        email_value = Email(email)
        now = self._now()
        invalid = InvalidResetCodeError("El correo o el código no son válidos.")

        user = self._users.get_by_email(email_value)
        if user is None:
            raise invalid
        active = self._codes.get_active(user.id, now)
        if active is None:
            raise invalid
        if not hmac.compare_digest(active.code_hash, hash_code(code)):
            self._codes.register_failure(active.id, now, MAX_FAILED_ATTEMPTS)
            raise invalid
        # El UPDATE condicional impide que dos peticiones usen el mismo código.
        if not self._codes.mark_used(active.id, now):
            raise invalid

        user.password_hash = self._hasher.hash(new_password)
        self._users.save(user)
        self._sessions.revoke_all(user.id, now)
