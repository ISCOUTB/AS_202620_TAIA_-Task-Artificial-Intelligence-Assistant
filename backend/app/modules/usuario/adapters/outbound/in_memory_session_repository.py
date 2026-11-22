"""Adaptador en memoria de sesiones, para pruebas unitarias."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.usuario.application.ports.outbound.session_repository import (
    RefreshTokenRecord,
    SessionRepository,
)


@dataclass
class _StoredToken:
    session_id: uuid.UUID
    expires_at: datetime
    used: bool = False


@dataclass
class _StoredSession:
    user_id: uuid.UUID
    revoked: bool = False
    fcm_token: str | None = None


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[uuid.UUID, _StoredSession] = {}
        self._tokens: dict[str, _StoredToken] = {}

    def create(
        self, session_id: uuid.UUID, user_id: uuid.UUID, refresh_token: str, expires_at: datetime
    ) -> None:
        self._sessions[session_id] = _StoredSession(user_id)
        self._tokens[refresh_token] = _StoredToken(session_id, expires_at)

    def is_active(self, session_id: uuid.UUID) -> bool:
        stored = self._sessions.get(session_id)
        return stored is not None and not stored.revoked

    def get_refresh_token(self, refresh_token: str) -> RefreshTokenRecord | None:
        token = self._tokens.get(refresh_token)
        if token is None:
            return None
        stored = self._sessions[token.session_id]
        return RefreshTokenRecord(token.session_id, stored.user_id, token.expires_at, token.used, stored.revoked)

    def rotate_refresh_token(
        self, old_token: str, new_token: str, expires_at: datetime, used_at: datetime
    ) -> bool:
        token = self._tokens.get(old_token)
        if token is None or token.used:
            return False
        token.used = True
        self._tokens[new_token] = _StoredToken(token.session_id, expires_at)
        return True

    def revoke(self, session_id: uuid.UUID, revoked_at: datetime) -> None:
        stored = self._sessions.get(session_id)
        if stored is not None:
            stored.revoked = True
            stored.fcm_token = None

    def revoke_all(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        for session_id, stored in self._sessions.items():
            if stored.user_id == user_id:
                self.revoke(session_id, revoked_at)

    def revoke_others(self, user_id: uuid.UUID, keep_session_id: uuid.UUID, revoked_at: datetime) -> None:
        for session_id, stored in self._sessions.items():
            if stored.user_id == user_id and session_id != keep_session_id:
                self.revoke(session_id, revoked_at)

    def set_fcm_token(self, session_id: uuid.UUID, fcm_token: str) -> None:
        self.invalidate_fcm_token(fcm_token)
        stored = self._sessions.get(session_id)
        if stored is not None and not stored.revoked:
            stored.fcm_token = fcm_token

    def clear_fcm_token(self, session_id: uuid.UUID) -> None:
        stored = self._sessions.get(session_id)
        if stored is not None:
            stored.fcm_token = None

    def get_fcm_tokens(self, user_id: uuid.UUID) -> list[str]:
        return [
            stored.fcm_token
            for stored in self._sessions.values()
            if stored.user_id == user_id and not stored.revoked and stored.fcm_token is not None
        ]

    def invalidate_fcm_token(self, fcm_token: str) -> None:
        for stored in self._sessions.values():
            if stored.fcm_token == fcm_token:
                stored.fcm_token = None
