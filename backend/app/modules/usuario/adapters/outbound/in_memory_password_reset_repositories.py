"""Adaptadores en memoria de la recuperación de contraseña, para pruebas unitarias (RF-USR-08)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.usuario.application.ports.outbound.password_reset_code_repository import (
    ActiveResetCode,
    PasswordResetCodeRepository,
)
from app.modules.usuario.application.ports.outbound.password_reset_request_repository import (
    PasswordResetRequestRepository,
)


class InMemoryPasswordResetRequestRepository(PasswordResetRequestRepository):
    def __init__(self) -> None:
        self._requests: list[tuple[str, datetime]] = []

    def add(self, email: str, requested_at: datetime) -> None:
        self._requests.append((email, requested_at))

    def count_since(self, email: str, since: datetime) -> int:
        return sum(1 for item, at in self._requests if item == email and at >= since)


@dataclass
class _StoredCode:
    id: uuid.UUID
    user_id: uuid.UUID
    code_hash: str
    created_at: datetime
    expires_at: datetime
    failed_attempts: int = 0
    used_at: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        return self.used_at is None and self.expires_at > now


class InMemoryPasswordResetCodeRepository(PasswordResetCodeRepository):
    def __init__(self) -> None:
        self.codes: list[_StoredCode] = []

    def replace(
        self, user_id: uuid.UUID, code_hash: str, created_at: datetime, expires_at: datetime
    ) -> None:
        for code in self.codes:
            if code.user_id == user_id and code.is_active(created_at):
                code.expires_at = created_at
        self.codes.append(_StoredCode(uuid.uuid4(), user_id, code_hash, created_at, expires_at))

    def get_active(self, user_id: uuid.UUID, now: datetime) -> ActiveResetCode | None:
        active = [code for code in self.codes if code.user_id == user_id and code.is_active(now)]
        if not active:
            return None
        latest = max(active, key=lambda code: code.created_at)
        return ActiveResetCode(latest.id, latest.code_hash)

    def register_failure(self, code_id: uuid.UUID, now: datetime, max_attempts: int) -> None:
        code = self._find(code_id)
        if code is None or not code.is_active(now):
            return
        code.failed_attempts += 1
        if code.failed_attempts >= max_attempts:
            code.expires_at = now

    def mark_used(self, code_id: uuid.UUID, now: datetime) -> bool:
        code = self._find(code_id)
        if code is None or not code.is_active(now):
            return False
        code.used_at = now
        return True

    def _find(self, code_id: uuid.UUID) -> _StoredCode | None:
        return next((code for code in self.codes if code.id == code_id), None)
