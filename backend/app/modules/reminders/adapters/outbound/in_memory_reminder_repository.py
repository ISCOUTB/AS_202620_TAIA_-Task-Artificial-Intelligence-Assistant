"""Repositorios en memoria de Reminders, para las pruebas unitarias."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from app.modules.reminders.application.ports.outbound.reminder_repository import (
    NotificationRepository,
    ReminderRepository,
)
from app.modules.reminders.domain.entities import (
    Notification,
    Reminder,
    ReminderOrigin,
    ReminderStatus,
)


class InMemoryReminderRepository(ReminderRepository, NotificationRepository):
    """Guarda `reminders` y `notifications` en el proceso, con las mismas reglas que SQL."""

    def __init__(self) -> None:
        self.reminders: dict[UUID, Reminder] = {}
        self.notifications: dict[UUID, Notification] = {}

    def add_all(self, reminders: list[Reminder]) -> None:
        for reminder in reminders:
            self.reminders[reminder.id] = reminder

    def get(self, reminder_id: UUID) -> Reminder | None:
        return self.reminders.get(reminder_id)

    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        return _sorted(r for r in self.reminders.values() if r.user_id == user_id)

    def list_by_task(self, task_id: UUID) -> list[Reminder]:
        return _sorted(r for r in self.reminders.values() if r.task_id == task_id)

    def update_pending(self, reminder: Reminder) -> bool:
        current = self.reminders.get(reminder.id)
        if current is None or not current.is_pending:
            return False
        self.reminders[reminder.id] = reminder
        return True

    def delete_unsent(self, reminder_id: UUID) -> bool:
        current = self.reminders.get(reminder_id)
        if current is not None and current.status is ReminderStatus.SENT:
            return False
        self.reminders.pop(reminder_id, None)
        return True

    def cancel(self, reminder_ids: list[UUID]) -> int:
        changed = 0
        for reminder_id in reminder_ids:
            current = self.reminders.get(reminder_id)
            if current is not None and current.is_pending:
                self.reminders[reminder_id] = replace(current, status=ReminderStatus.CANCELLED)
                changed += 1
        return changed

    def cancel_pending_for_user(self, user_id: UUID) -> None:
        self.cancel([r.id for r in self.reminders.values() if r.user_id == user_id])

    def replace_automatic(self, task_id: UUID, reminders: list[Reminder]) -> None:
        for reminder in list(self.reminders.values()):
            if (reminder.task_id == task_id and reminder.origin is ReminderOrigin.AUTOMATIC
                    and reminder.status is not ReminderStatus.SENT):
                del self.reminders[reminder.id]
        self.add_all(reminders)

    def list_due(self, now: datetime) -> list[Reminder]:
        return _sorted(r for r in self.reminders.values() if r.is_pending and r.scheduled_at <= now)

    def claim(self, reminder_id: UUID, notification: Notification) -> bool:
        current = self.reminders.get(reminder_id)
        if current is None or not current.is_pending:
            return False
        self.reminders[reminder_id] = replace(current, status=ReminderStatus.SENT)
        self.notifications[notification.id] = notification
        return True

    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> tuple[list[Notification], int]:
        own = sorted(
            (n for n in self.notifications.values() if self._owner(n) == user_id),
            key=lambda n: (n.created_at, n.id),
            reverse=True,
        )
        return own[offset:offset + limit], len(own)

    def mark_read(self, notification_id: UUID, user_id: UUID, now: datetime) -> Notification | None:
        current = self.notifications.get(notification_id)
        if current is None or self._owner(current) != user_id:
            return None
        if current.read_at is None:
            current = replace(current, read_at=now)
            self.notifications[notification_id] = current
        return current

    def mark_all_read(self, user_id: UUID, now: datetime) -> None:
        for notification in list(self.notifications.values()):
            if self._owner(notification) == user_id and notification.read_at is None:
                self.notifications[notification.id] = replace(notification, read_at=now)

    def count_unread(self, user_id: UUID) -> int:
        return sum(1 for n in self.notifications.values() if self._owner(n) == user_id and not n.read)

    def record_push(self, notification_id: UUID, attempts: int, sent_at: datetime | None) -> None:
        current = self.notifications[notification_id]
        self.notifications[notification_id] = replace(current, push_attempts=attempts, push_sent_at=sent_at)

    def _owner(self, notification: Notification) -> UUID | None:
        reminder = self.reminders.get(notification.reminder_id)
        return reminder.user_id if reminder is not None else None


def _sorted(reminders) -> list[Reminder]:
    return sorted(reminders, key=lambda r: (r.scheduled_at, r.id))
