"""RF-REC-03 · Consultar un recordatorio propio (RT-02)."""

from __future__ import annotations

from uuid import UUID

from app.modules.reminders.application.errors import ReminderNotFoundError
from app.modules.reminders.application.ports.inbound.reminder_ports import GetReminderPort
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.domain.entities import Reminder


def get_owned(repository: ReminderRepository, reminder_id: UUID, user_id: UUID) -> Reminder:
    reminder = repository.get(reminder_id)
    if reminder is None or reminder.user_id != user_id:
        raise ReminderNotFoundError("El recordatorio no existe o no pertenece al usuario.")
    return reminder


class GetReminderUseCase(GetReminderPort):
    def __init__(self, repository: ReminderRepository) -> None:
        self._repository = repository

    def execute(self, reminder_id: UUID, user_id: UUID) -> Reminder:
        return get_owned(self._repository, reminder_id, user_id)
