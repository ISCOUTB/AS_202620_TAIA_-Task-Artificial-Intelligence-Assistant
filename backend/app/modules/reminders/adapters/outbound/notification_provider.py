"""Composition root for notification delivery."""

from backend.app.modules.reminders.adapters.outbound.repository_provider import get_reminder_repository
from backend.app.modules.reminders.adapters.outbound.telegram_bot_client import TelegramBotApiClient
from backend.app.modules.reminders.adapters.outbound.telegram_notification_sender import TelegramNotificationSender
from backend.app.modules.usuario.application.ports.inbound.identity import get_identity_service


def get_notification_sender() -> TelegramNotificationSender:
    identity_service = get_identity_service()
    repository = get_reminder_repository()
    return TelegramNotificationSender(
        bot_client=TelegramBotApiClient(),
        telegram_user_id_resolver=identity_service.get_telegram_user_id,
        reminder_user_id_resolver=lambda reminder_id: (
            repository.get_by_id(reminder_id).user_id
            if repository.get_by_id(reminder_id) is not None
            else None
        ),
    )
