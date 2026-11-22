"""Reglas de RF-REC-01 compartidas por crear, editar y los recordatorios del plan `custom`."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.modules.reminders.application.errors import (
    InvalidReminderError,
    ReminderStateError,
    ReminderTaskNotFoundError,
)
from app.modules.reminders.application.ports.outbound.academic_task_lookup import (
    AcademicTaskLookup,
    TaskInfo,
)
from app.modules.reminders.domain.entities.reminder import MAX_MESSAGE_LENGTH
from app.shared.clock import as_bogota


def require_open_task(tasks: AcademicTaskLookup, task_id: UUID, user_id: UUID) -> TaskInfo:
    """La actividad es propia, no está eliminada y sigue pendiente."""

    task = tasks.get(task_id, user_id)
    if task is None:
        raise ReminderTaskNotFoundError("La actividad no existe o no pertenece al usuario.")
    if task.completed:
        raise ReminderStateError("La actividad ya está completada.")
    return task


def validate_schedule(scheduled_at: datetime, now: datetime, due_at: datetime) -> datetime:
    """La fecha es futura y anterior a la fecha límite. Sin zona, es hora de Colombia (RT-03)."""

    scheduled = as_bogota(scheduled_at)
    if scheduled <= now:
        raise InvalidReminderError("La fecha del recordatorio debe ser futura.")
    if scheduled >= due_at:
        raise InvalidReminderError(
            "La fecha del recordatorio debe ser anterior a la fecha límite de la actividad."
        )
    return scheduled


def clean_message(message: str | None) -> str | None:
    if message is None:
        return None
    text = message.strip()
    if not text:
        raise InvalidReminderError("El mensaje del recordatorio no puede estar vacío.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise InvalidReminderError(
            f"El mensaje del recordatorio no puede superar {MAX_MESSAGE_LENGTH} caracteres."
        )
    return text
