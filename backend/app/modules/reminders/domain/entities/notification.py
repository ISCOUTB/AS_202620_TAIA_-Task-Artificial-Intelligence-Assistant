"""Notificación generada por un recordatorio (diccionario de datos §7.2, RF-NOT-02…04)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Notification:
    """Fila de `notifications`. `message` es una copia histórica del texto enviado."""

    id: UUID
    reminder_id: UUID
    message: str
    created_at: datetime
    push_attempts: int = 0
    push_sent_at: datetime | None = None
    read_at: datetime | None = None

    @property
    def read(self) -> bool:
        """Campo derivado `read` del diccionario §9 (RF-NOT-03)."""

        return self.read_at is not None
