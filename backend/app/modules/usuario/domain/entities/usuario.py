"""Entidad y reglas del dominio Usuario."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from backend.app.modules.usuario.domain.value_objects.email import Email


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class InvalidUserError(ValueError):
    """Se lanza cuando los datos del usuario violan una regla del dominio."""


@dataclass
class Usuario:
    """Usuario propietario de su identidad dentro de TAIA."""

    id: uuid.UUID
    name: str
    email: Email
    password_hash: str
    status: UserStatus = UserStatus.ACTIVE
    telegram_user_id: int | None = None

    MAX_NAME_LENGTH = 100

    @staticmethod
    def create(name: str, email: Email, password_hash: str) -> "Usuario":
        clean_name = (name or "").strip()
        if not clean_name:
            raise InvalidUserError("El nombre del usuario no puede estar vacío.")
        if len(clean_name) > Usuario.MAX_NAME_LENGTH:
            raise InvalidUserError(
                f"El nombre no puede superar {Usuario.MAX_NAME_LENGTH} caracteres."
            )
        if not password_hash:
            raise InvalidUserError("El usuario debe tener una contraseña protegida.")

        return Usuario(
            id=uuid.uuid4(),
            name=clean_name,
            email=email,
            password_hash=password_hash,
        )

    def link_telegram(self, telegram_user_id: int) -> None:
        """Vincula una cuenta Telegram existente con este usuario."""
        if telegram_user_id <= 0:
            raise InvalidUserError("El identificador de Telegram no es válido.")
        self.telegram_user_id = telegram_user_id

    def unlink_telegram(self) -> None:
        """Elimina la vinculación actual con Telegram."""
        self.telegram_user_id = None
