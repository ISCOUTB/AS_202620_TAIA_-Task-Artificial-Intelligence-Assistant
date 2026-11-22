"""Implementación de `UserDeviceDirectory`, el puerto que usa Reminders (RF-NOT-01, 02, 04)."""

from __future__ import annotations

from uuid import UUID

from app.modules.usuario.application.ports.outbound.session_repository import SessionRepository
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.domain.entities.usuario import UserStatus


class UserDeviceDirectoryService:
    """Expone los dispositivos y el estado de la cuenta sin dar acceso a la tabla `sessions`."""

    def __init__(self, users: UserRepository, sessions: SessionRepository) -> None:
        self._users = users
        self._sessions = sessions

    def get_fcm_tokens(self, user_id: UUID) -> list[str]:
        return self._sessions.get_fcm_tokens(user_id)

    def invalidate_fcm_token(self, fcm_token: str) -> None:
        self._sessions.invalidate_fcm_token(fcm_token)

    def is_active(self, user_id: UUID) -> bool:
        # RF-USR-09: activa significa `deactivated_at IS NULL`.
        user = self._users.get_by_id(user_id)
        return user is not None and user.status is UserStatus.ACTIVE
