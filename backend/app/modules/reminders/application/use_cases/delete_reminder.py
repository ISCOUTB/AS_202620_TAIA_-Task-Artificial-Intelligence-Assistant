from uuid import UUID

from backend.app.modules.reminders.application.ports.inbound.reminder_ports import (
    DeleteReminderPort,
)
from backend.app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)


class DeleteReminderUseCase(DeleteReminderPort):
    """Deletes a reminder, validating it belongs to the user."""

    def __init__(self, repository: ReminderRepository):
        self._repository = repository

    def execute(self, reminder_id: int, user_id: UUID) -> None:
        reminder = self._repository.get_by_id(reminder_id)
        if reminder is None or reminder.user_id != user_id:
            raise ValueError("Recordatorio no encontrado")

        self._repository.delete(reminder_id)
