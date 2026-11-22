"""RF-NOT-03 · Bandeja de notificaciones."""

from __future__ import annotations

from uuid import UUID

from app.modules.reminders.application.errors import NotificationNotFoundError
from app.modules.reminders.application.ports.inbound.reminder_ports import (
    NotificationInboxPort,
    NotificationPage,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import NotificationRepository
from app.modules.reminders.domain.entities import Notification
from app.shared.clock import Clock, now_bogota


class NotificationInboxUseCase(NotificationInboxPort):
    """El usuario de una notificación se obtiene a través de su recordatorio (RT-02)."""

    def __init__(self, repository: NotificationRepository, clock: Clock = now_bogota) -> None:
        self._repository = repository
        self._clock = clock

    def list(self, user_id: UUID, limit: int, offset: int) -> NotificationPage:
        items, total = self._repository.list_for_user(user_id, limit, offset)
        return NotificationPage(items=items, total=total, limit=limit, offset=offset)

    def mark_read(self, notification_id: UUID, user_id: UUID) -> Notification:
        notification = self._repository.mark_read(notification_id, user_id, self._clock())
        if notification is None:
            raise NotificationNotFoundError("La notificación no existe o no pertenece al usuario.")
        return notification

    def mark_all_read(self, user_id: UUID) -> None:
        self._repository.mark_all_read(user_id, self._clock())

    def count_unread(self, user_id: UUID) -> int:
        return self._repository.count_unread(user_id)
