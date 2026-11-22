"""RF-REC-04 · Editar un recordatorio pendiente."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from app.modules.reminders.application.errors import ReminderStateError
from app.modules.reminders.application.ports.inbound.reminder_ports import EditReminderPort
from app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.application.reminder_rules import (
    clean_message,
    require_open_task,
    validate_schedule,
)
from app.modules.reminders.application.use_cases.get_reminder import get_owned
from app.modules.reminders.domain.entities import Reminder, ReminderOrigin
from app.shared.clock import Clock, now_bogota

NOT_PENDING = "Solo se puede editar un recordatorio pendiente."


class EditReminderUseCase(EditReminderPort):
    """Aplican las reglas de RF-REC-01. Un automático editado pasa a `custom`."""

    def __init__(
        self, repository: ReminderRepository, tasks: AcademicTaskLookup, clock: Clock = now_bogota
    ) -> None:
        self._repository = repository
        self._tasks = tasks
        self._clock = clock

    def execute(
        self,
        reminder_id: UUID,
        user_id: UUID,
        scheduled_at: datetime | None,
        custom_message: str | None,
    ) -> Reminder:
        reminder = get_owned(self._repository, reminder_id, user_id)
        if not reminder.is_pending:
            raise ReminderStateError(NOT_PENDING)
        if scheduled_at is None and custom_message is None:
            return reminder
        message = clean_message(custom_message)
        task = require_open_task(self._tasks, reminder.task_id, user_id)
        edited = replace(
            reminder,
            scheduled_at=validate_schedule(scheduled_at or reminder.scheduled_at, self._clock(), task.due_at),
            custom_message=message if message is not None else reminder.custom_message,
            origin=ReminderOrigin.CUSTOM,
        )
        if not self._repository.update_pending(edited):
            raise ReminderStateError(NOT_PENDING)
        return edited
