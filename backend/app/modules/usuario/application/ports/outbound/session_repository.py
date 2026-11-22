"""Puerto para sesiones y tokens de renovación (RF-USR-03, 04)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RefreshTokenRecord:
    session_id: uuid.UUID
    user_id: uuid.UUID
    expires_at: datetime
    used: bool
    session_revoked: bool


class SessionRepository(ABC):
    @abstractmethod
    def create(
        self, session_id: uuid.UUID, user_id: uuid.UUID, refresh_token: str, expires_at: datetime
    ) -> None:
        """Abre una sesión con su primer token de renovación (se guarda como hash)."""

    @abstractmethod
    def is_active(self, session_id: uuid.UUID) -> bool:
        """Indica si la sesión existe y no está revocada."""

    @abstractmethod
    def get_refresh_token(self, refresh_token: str) -> RefreshTokenRecord | None:
        """Busca un token de renovación por su hash."""

    @abstractmethod
    def rotate_refresh_token(
        self, old_token: str, new_token: str, expires_at: datetime, used_at: datetime
    ) -> bool:
        """Marca el token como usado y emite el siguiente en la misma sesión.

        Devuelve False si otro proceso ya lo había usado: es una reutilización.
        """

    @abstractmethod
    def revoke(self, session_id: uuid.UUID, revoked_at: datetime) -> None:
        """Revoca la sesión y olvida su token FCM (RF-NOT-01)."""

    @abstractmethod
    def revoke_all(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        """Revoca todas las sesiones activas del usuario."""

    @abstractmethod
    def revoke_others(self, user_id: uuid.UUID, keep_session_id: uuid.UUID, revoked_at: datetime) -> None:
        """Revoca las sesiones activas del usuario salvo `keep_session_id` (RF-USR-07)."""

    @abstractmethod
    def set_fcm_token(self, session_id: uuid.UUID, fcm_token: str) -> None:
        """Asocia el token FCM a la sesión activa; si estaba en otra sesión, lo quita de allí (RF-NOT-01)."""

    @abstractmethod
    def clear_fcm_token(self, session_id: uuid.UUID) -> None:
        """Quita el token FCM de la sesión (RF-NOT-01)."""

    @abstractmethod
    def get_fcm_tokens(self, user_id: uuid.UUID) -> list[str]:
        """Tokens FCM de las sesiones no revocadas del usuario."""

    @abstractmethod
    def invalidate_fcm_token(self, fcm_token: str) -> None:
        """Pone en `NULL` el token en la sesión que lo tenga."""
