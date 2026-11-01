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


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[uuid.UUID, tuple[uuid.UUID, bool]] = {}
        self._tokens: dict[str, _StoredToken] = {}

    def create(
        self, session_id: uuid.UUID, user_id: uuid.UUID, refresh_token: str, expires_at: datetime
    ) -> None:
        self._sessions[session_id] = (user_id, False)
        self._tokens[refresh_token] = _StoredToken(session_id, expires_at)

    def is_active(self, session_id: uuid.UUID) -> bool:
        stored = self._sessions.get(session_id)
        return stored is not None and not stored[1]

    def get_refresh_token(self, refresh_token: str) -> RefreshTokenRecord | None:
        token = self._tokens.get(refresh_token)
        if token is None:
            return None
        user_id, revoked = self._sessions[token.session_id]
        return RefreshTokenRecord(token.session_id, user_id, token.expires_at, token.used, revoked)

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
        if session_id in self._sessions:
            self._sessions[session_id] = (self._sessions[session_id][0], True)

    def revoke_all(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        for session_id, (owner, _) in self._sessions.items():
            if owner == user_id:
                self._sessions[session_id] = (owner, True)
