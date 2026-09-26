"""Outbound port for Reminder persistence.

The application layer depends on this interface, never on SQLAlchemy,
Postgres, etc. Those details are implemented in `adapters/outbound`.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.reminders.domain.entities import Notification, Reminder


class ReminderRepository(ABC):
    """Outbound port of the reminders module for persistence."""

    @abstractmethod
    def next_id(self) -> UUID:
        """Generates/reserves an identifier for a new Reminder."""
        raise NotImplementedError

    @abstractmethod
    def create(self, reminder: Reminder) -> Reminder:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, reminder_id: UUID) -> Reminder | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        raise NotImplementedError

    @abstractmethod
    def update(self, reminder: Reminder) -> Reminder:
        raise NotImplementedError

    @abstractmethod
    def delete(self, reminder_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_notification(self, notification: Notification) -> Notification:
        raise NotImplementedError

    @abstractmethod
    def record_notification_attempt(self, notification: Notification, sent: bool) -> None:
        raise NotImplementedError
