"""In-memory outbound adapter for the Reminders repository.

This adapter is intentionally small and deterministic so the Reminders
module can be executed and tested before PostgreSQL/SQLAlchemy is wired.
"""

import uuid
from uuid import UUID

from app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Notification, Reminder


class InMemoryReminderRepository(ReminderRepository):
    """Stores reminders in process memory, scoped by reminder id."""

    def __init__(self) -> None:
        self._items: dict[UUID, Reminder] = {}
        self._notifications: dict[UUID, Notification] = {}

    def next_id(self) -> UUID:
        return uuid.uuid4()

    def create(self, reminder: Reminder) -> Reminder:
        if reminder.id in self._items:
            raise ValueError("El recordatorio ya existe")
        self._items[reminder.id] = reminder
        return reminder

    def get_by_id(self, reminder_id: UUID) -> Reminder | None:
        return self._items.get(reminder_id)

    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        return [item for item in self._items.values() if item.user_id == user_id]

    def update(self, reminder: Reminder) -> Reminder:
        if reminder.id not in self._items:
            raise ValueError("Recordatorio no encontrado")
        self._items[reminder.id] = reminder
        return reminder

    def delete(self, reminder_id: UUID) -> None:
        self._items.pop(reminder_id, None)

    def create_notification(self, notification: Notification) -> Notification:
        return self._notifications.setdefault(notification.reminder_id, notification)

    def record_notification_attempt(self, notification: Notification, sent: bool) -> None:
        if sent and notification.reminder_id in self._items:
            self._items[notification.reminder_id] = self._items[notification.reminder_id].mark_completed()
