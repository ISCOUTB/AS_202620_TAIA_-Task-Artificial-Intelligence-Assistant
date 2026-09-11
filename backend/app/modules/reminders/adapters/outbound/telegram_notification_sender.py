"""Outbound adapter for Telegram notification delivery."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from backend.app.modules.reminders.application.ports.outbound.notification_sender import NotificationSender
from backend.app.modules.reminders.domain.entities import Notification


class TelegramNotificationSender(NotificationSender):
    def __init__(
        self,
        bot_client,
        telegram_user_id_resolver: Callable[[UUID], int | None],
        reminder_user_id_resolver: Callable[[int], UUID | None],
    ) -> None:
        self._bot_client = bot_client
        self._telegram_user_id_resolver = telegram_user_id_resolver
        self._reminder_user_id_resolver = reminder_user_id_resolver

    def send(self, notification: Notification) -> bool:
        user_id = self._reminder_user_id_resolver(notification.reminder_id)
        if user_id is None:
            return False

        chat_id = self._telegram_user_id_resolver(user_id)
        if chat_id is None:
            return False

        try:
            self._bot_client.send_message(chat_id=chat_id, text=notification.message)
        except Exception:
            return False
        return True
