"""RF-REC-03 · Listar los recordatorios del usuario."""

from __future__ import annotations

from uuid import UUID

from app.modules.reminders.application.ports.inbound.reminder_ports import ListRemindersPort
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.domain.entities import Reminder


class ListRemindersUseCase(ListRemindersPort):
    def __init__(self, repository: ReminderRepository) -> None:
        self._repository = repository

    def execute(self, user_id: UUID) -> list[Reminder]:
        return self._repository.list_by_user(user_id)
