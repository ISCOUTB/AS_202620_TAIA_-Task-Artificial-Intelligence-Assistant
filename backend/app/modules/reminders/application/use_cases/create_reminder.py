"""RF-REC-01 · Crear recordatorio personalizado."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from app.modules.reminders.application.ports.inbound.reminder_ports import CreateReminderPort
from app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.application.reminder_rules import (
    clean_message,
    require_open_task,
    validate_schedule,
)
from app.modules.reminders.domain.entities import Reminder, ReminderOrigin
from app.shared.clock import Clock, now_bogota


class CreateReminderUseCase(CreateReminderPort):
    def __init__(
        self, repository: ReminderRepository, tasks: AcademicTaskLookup, clock: Clock = now_bogota
    ) -> None:
        self._repository = repository
        self._tasks = tasks
        self._clock = clock

    def execute(
        self, user_id: UUID, task_id: UUID, scheduled_at: datetime, custom_message: str | None
    ) -> Reminder:
        message = clean_message(custom_message)
        task = require_open_task(self._tasks, task_id, user_id)
        reminder = Reminder(
            id=uuid.uuid4(),
            user_id=user_id,
            task_id=task_id,
            scheduled_at=validate_schedule(scheduled_at, self._clock(), task.due_at),
            origin=ReminderOrigin.CUSTOM,
            custom_message=message,
        )
        self._repository.add_all([reminder])
        return reminder
