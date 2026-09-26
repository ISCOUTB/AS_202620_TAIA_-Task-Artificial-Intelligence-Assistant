from uuid import UUID

from app.modules.reminders.application.ports.inbound.reminder_ports import (
    GetReminderPort,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Reminder


class GetReminderUseCase(GetReminderPort):
    """Fetches a single reminder, validating it belongs to the user."""

    def __init__(self, repository: ReminderRepository):
        self._repository = repository

    def execute(self, reminder_id: int, user_id: UUID) -> Reminder:
        reminder = self._repository.get_by_id(reminder_id)
        if reminder is None or reminder.user_id != user_id:
            raise ValueError("Recordatorio no encontrado")
        return reminder
