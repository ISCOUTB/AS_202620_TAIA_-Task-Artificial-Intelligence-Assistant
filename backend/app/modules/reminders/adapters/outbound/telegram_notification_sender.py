"""Outbound adapter: notification delivery via Telegram.

This is the only class in the reminders module that knows about the
Telegram bot/SDK.
"""

from app.modules.reminders.application.ports.outbound.notification_sender import (
    NotificationSender,
)
from app.modules.reminders.domain.entities import Notification


class TelegramNotificationSender(NotificationSender):
    def __init__(self, bot_client, chat_id_resolver):
        """
        bot_client: already configured Telegram client/SDK.
        chat_id_resolver: callable(reminder_id) -> Telegram chat_id of
                           the user who owns the reminder.
        """
        self._bot_client = bot_client
        self._chat_id_resolver = chat_id_resolver

    def send(self, notification: Notification) -> bool:
        chat_id = self._chat_id_resolver(notification.reminder_id)
        try:
            self._bot_client.send_message(chat_id=chat_id, text=notification.message)
            return True
        except Exception:
            return False
