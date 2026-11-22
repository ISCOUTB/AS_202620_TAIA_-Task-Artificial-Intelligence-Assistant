"""Casos de uso del token FCM del dispositivo de la sesión actual (RF-NOT-01)."""

from __future__ import annotations

import uuid

from app.modules.usuario.application.ports.outbound.session_repository import SessionRepository


class InvalidFcmTokenError(ValueError):
    """El token FCM está vacío."""


class RegisterFcmTokenUseCase:
    """Asocia el token FCM a la sesión; si otra sesión lo tenía, se mueve a esta."""

    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, session_id: uuid.UUID, fcm_token: str) -> None:
        clean_token = fcm_token.strip()
        if not clean_token:
            raise InvalidFcmTokenError("El token del dispositivo no puede estar vacío.")
        self._sessions.set_fcm_token(session_id, clean_token)


class RemoveFcmTokenUseCase:
    """Quita el token FCM de la sesión: el dispositivo deja de recibir notificaciones."""

    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, session_id: uuid.UUID) -> None:
        self._sessions.clear_fcm_token(session_id)
