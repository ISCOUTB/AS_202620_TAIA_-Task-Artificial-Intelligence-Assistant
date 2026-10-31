"""Adaptador en memoria de los intentos fallidos, para pruebas unitarias."""

from __future__ import annotations

from datetime import datetime

from app.modules.usuario.application.ports.outbound.failed_login_attempt_repository import (
    FailedLoginAttemptRepository,
)


class InMemoryFailedLoginAttemptRepository(FailedLoginAttemptRepository):
    def __init__(self) -> None:
        self._attempts: list[tuple[str, datetime]] = []

    def add(self, email: str, attempted_at: datetime) -> None:
        self._attempts.append((email, attempted_at))

    def count_since(self, email: str, since: datetime) -> int:
        return sum(1 for item, at in self._attempts if item == email and at >= since)
