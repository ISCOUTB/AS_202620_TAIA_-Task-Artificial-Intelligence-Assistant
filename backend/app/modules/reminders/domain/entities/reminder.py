"""Recordatorio de una actividad (diccionario de datos §7.1, RF-REC-01…07)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from app.shared.clock import as_bogota

MAX_MESSAGE_LENGTH = 500


class ReminderOrigin(str, Enum):
    """Valores del ENUM `reminder_origin`."""

    AUTOMATIC = "automatic"
    CUSTOM = "custom"


class ReminderStatus(str, Enum):
    """Valores del ENUM `reminder_status`."""

    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Reminder:
    """Fila de `reminders`. `custom_message` en `None` usa el mensaje por defecto."""

    id: UUID
    user_id: UUID
    task_id: UUID
    scheduled_at: datetime
    origin: ReminderOrigin
    status: ReminderStatus = ReminderStatus.PENDING
    custom_message: str | None = None

    @property
    def is_pending(self) -> bool:
        return self.status is ReminderStatus.PENDING


def default_message(title: str, subject_name: str, due_at: datetime) -> str:
    """Mensaje por defecto de RF-REC-01 y del diccionario §9, en hora de Colombia (RT-03).

    Con la voz de TAIA (RF-AGT-22); el emoji del pulpo va como secuencia de escape.
    """

    return (
        f"¡Ey! Soy TAIA 🐙 Recuerda que {title} de {subject_name} vence el "
        f"{as_bogota(due_at):%d/%m/%Y %H:%M}. ¡Tú puedes!"
    )
