"""Puerto para los códigos de verificación de la recuperación de contraseña (RF-USR-08)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ActiveResetCode:
    id: uuid.UUID
    code_hash: str


class PasswordResetCodeRepository(ABC):
    @abstractmethod
    def replace(
        self, user_id: uuid.UUID, code_hash: str, created_at: datetime, expires_at: datetime
    ) -> None:
        """Invalida los códigos vigentes del usuario y guarda el nuevo, en una transacción."""

    @abstractmethod
    def get_active(self, user_id: uuid.UUID, now: datetime) -> ActiveResetCode | None:
        """El código vigente del usuario: sin usar y sin vencer."""

    @abstractmethod
    def register_failure(self, code_id: uuid.UUID, now: datetime, max_attempts: int) -> None:
        """Suma un intento fallido; al llegar a `max_attempts`, el código vence en `now`."""

    @abstractmethod
    def mark_used(self, code_id: uuid.UUID, now: datetime) -> bool:
        """Marca el código como usado. Devuelve False si ya no estaba vigente."""
