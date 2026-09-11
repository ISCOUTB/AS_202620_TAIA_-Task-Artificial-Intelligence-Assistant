from app.modules.reminders.application.ports.inbound.reminder_ports import (
    SendNotificationPort,
)
from app.modules.reminders.application.ports.outbound.notification_sender import (
    NotificationSender,
)
from app.modules.reminders.domain.entities import Notification


class SendNotificationUseCase(SendNotificationPort):
    """Delivers an already scheduled notification through the configured channel."""

    def __init__(self, sender: NotificationSender):
        self._sender = sender

    def execute(self, notification: Notification) -> bool:
        return self._sender.send(notification)
