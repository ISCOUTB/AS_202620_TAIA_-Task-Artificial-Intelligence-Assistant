from uuid import UUID

from backend.app.modules.reminders.application.ports.inbound.reminder_ports import (
    MarkReminderCompletedPort,
)
from backend.app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from backend.app.modules.reminders.domain.entities import Reminder


class MarkReminderCompletedUseCase(MarkReminderCompletedPort):
    """Marks a reminder as completed. Idempotent operation."""

    def __init__(self, repository: ReminderRepository):
        self._repository = repository

    def execute(self, reminder_id: int, user_id: UUID) -> Reminder:
        reminder = self._repository.get_by_id(reminder_id)
        if reminder is None or reminder.user_id != user_id:
            raise ValueError("Recordatorio no encontrado")

        if reminder.is_completed:
            return reminder

        updated = reminder.model_copy(update={"is_completed": True})
        return self._repository.update(updated)
