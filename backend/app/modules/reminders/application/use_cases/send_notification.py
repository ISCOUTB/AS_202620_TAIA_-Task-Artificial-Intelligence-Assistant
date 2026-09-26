from app.modules.reminders.application.ports.inbound.reminder_ports import (
    SendNotificationPort,
)
from app.modules.reminders.application.ports.outbound.notification_sender import (
    NotificationSender,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.domain.entities import Notification


class SendNotificationUseCase(SendNotificationPort):
    """Delivers an already scheduled notification through the configured channel."""

    def __init__(self, sender: NotificationSender, repository: ReminderRepository | None = None):
        self._sender = sender
        self._repository = repository

    def execute(self, notification: Notification) -> bool:
        sent = self._sender.send(notification)
        if self._repository is not None:
            self._repository.record_notification_attempt(notification, sent)
        return sent
