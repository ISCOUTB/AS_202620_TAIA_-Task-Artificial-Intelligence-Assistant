"""Puertos de entrada de los adaptadores HTTP de Reminders (RF-REC-01…05, RF-NOT-03)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.reminders.domain.entities import Notification, Reminder


class CreateReminderPort(ABC):
    @abstractmethod
    def execute(
        self, user_id: UUID, task_id: UUID, scheduled_at: datetime, custom_message: str | None
    ) -> Reminder:
        raise NotImplementedError


class ListRemindersPort(ABC):
    @abstractmethod
    def execute(self, user_id: UUID) -> list[Reminder]:
        raise NotImplementedError


class GetReminderPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: UUID, user_id: UUID) -> Reminder:
        raise NotImplementedError


class EditReminderPort(ABC):
    @abstractmethod
    def execute(
        self,
        reminder_id: UUID,
        user_id: UUID,
        scheduled_at: datetime | None,
        custom_message: str | None,
    ) -> Reminder:
        """`None` en un campo significa que no cambia."""
        raise NotImplementedError


class DeleteReminderPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: UUID, user_id: UUID) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class NotificationPage:
    items: list[Notification]
    total: int
    limit: int
    offset: int


class NotificationInboxPort(ABC):
    """Bandeja de notificaciones del usuario (RF-NOT-03)."""

    @abstractmethod
    def list(self, user_id: UUID, limit: int, offset: int) -> NotificationPage:
        raise NotImplementedError

    @abstractmethod
    def mark_read(self, notification_id: UUID, user_id: UUID) -> Notification:
        raise NotImplementedError

    @abstractmethod
    def mark_all_read(self, user_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_unread(self, user_id: UUID) -> int:
        raise NotImplementedError
