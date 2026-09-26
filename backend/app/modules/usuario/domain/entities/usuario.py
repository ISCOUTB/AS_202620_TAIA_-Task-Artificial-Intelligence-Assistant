"""Entidad y reglas del dominio Usuario."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import now_bogota


class UserStatus(str, Enum):
    """Estado derivado de `deactivated_at`; no se almacena (diccionario, sección 9)."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class InvalidUserError(ValueError):
    """Se lanza cuando los datos del usuario violan una regla del dominio."""


@dataclass
class Usuario:
    """Usuario propietario de su identidad dentro de TAIA."""

    id: uuid.UUID
    full_name: str
    email: Email
    password_hash: str
    telegram_user_id: int | None = None
    telegram_linked_at: datetime | None = None
    deactivated_at: datetime | None = None
    created_at: datetime = field(default_factory=now_bogota)

    MAX_FULL_NAME_LENGTH = 100

    @staticmethod
    def create(full_name: str, email: Email, password_hash: str) -> "Usuario":
        """Crea un usuario nuevo aplicando las reglas de RF-USR-01."""

        clean_name = (full_name or "").strip()
        if not clean_name:
            raise InvalidUserError("El nombre del usuario no puede estar vacío.")
        if len(clean_name) > Usuario.MAX_FULL_NAME_LENGTH:
            raise InvalidUserError(
                f"El nombre no puede superar {Usuario.MAX_FULL_NAME_LENGTH} caracteres."
            )
        if not password_hash:
            raise InvalidUserError("El usuario debe tener una contraseña protegida.")

        return Usuario(
            id=uuid.uuid4(),
            full_name=clean_name,
            email=email,
            password_hash=password_hash,
        )

    @property
    def status(self) -> UserStatus:
        return UserStatus.ACTIVE if self.deactivated_at is None else UserStatus.INACTIVE

    def link_telegram(self, telegram_user_id: int, now: datetime | None = None) -> None:
        """Vincula una cuenta Telegram existente con este usuario."""
        if telegram_user_id <= 0:
            raise InvalidUserError("El identificador de Telegram no es válido.")
        self.telegram_user_id = telegram_user_id
        self.telegram_linked_at = now or now_bogota()

    def unlink_telegram(self) -> None:
        """Elimina la vinculación actual con Telegram."""
        self.telegram_user_id = None
        self.telegram_linked_at = None
