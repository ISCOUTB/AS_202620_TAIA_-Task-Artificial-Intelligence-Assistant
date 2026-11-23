"""RF-REC-03 · Listar los recordatorios del usuario, filtrables por actividad y estado."""

from __future__ import annotations

from uuid import UUID

from app.modules.reminders.application.ports.inbound.reminder_ports import ListRemindersPort
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.domain.entities import Reminder, ReminderStatus


class ListRemindersUseCase(ListRemindersPort):
    def __init__(self, repository: ReminderRepository) -> None:
        self._repository = repository

    def execute(
        self, user_id: UUID, task_id: UUID | None = None, status: ReminderStatus | None = None
    ) -> list[Reminder]:
        # Se filtra sobre los recordatorios del usuario: una actividad de otro
        # usuario no devuelve nada (RT-02).
        return [
            reminder
            for reminder in self._repository.list_by_user(user_id)
            if (task_id is None or reminder.task_id == task_id)
            and (status is None or reminder.status == status)
        ]
