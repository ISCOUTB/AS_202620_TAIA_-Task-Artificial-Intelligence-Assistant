from uuid import UUID

from app.modules.reminders.application.ports.inbound.reminder_ports import (
    ListRemindersPort,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Reminder


class ListRemindersUseCase(ListRemindersPort):
    """Lists every reminder that belongs to a user."""

    def __init__(self, repository: ReminderRepository):
        self._repository = repository

    def execute(self, user_id: UUID) -> list[Reminder]:
        return self._repository.list_by_user(user_id)
