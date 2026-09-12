"""In-memory outbound adapter for the Reminders repository.

This adapter is intentionally small and deterministic so the Reminders
module can be executed and tested before PostgreSQL/SQLAlchemy is wired.
"""

from uuid import UUID

from backend.app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from backend.app.modules.reminders.domain.entities import Reminder


class InMemoryReminderRepository(ReminderRepository):
    """Stores reminders in process memory, scoped by reminder id."""

    def __init__(self) -> None:
        self._items: dict[int, Reminder] = {}
        self._next_id = 1

    def next_id(self) -> int:
        reminder_id = self._next_id
        self._next_id += 1
        return reminder_id

    def create(self, reminder: Reminder) -> Reminder:
        if reminder.id in self._items:
            raise ValueError("El recordatorio ya existe")
        self._items[reminder.id] = reminder
        return reminder

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        return self._items.get(reminder_id)

    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        return [item for item in self._items.values() if item.user_id == user_id]

    def update(self, reminder: Reminder) -> Reminder:
        if reminder.id not in self._items:
            raise ValueError("Recordatorio no encontrado")
        self._items[reminder.id] = reminder
        return reminder

    def delete(self, reminder_id: int) -> None:
        self._items.pop(reminder_id, None)
