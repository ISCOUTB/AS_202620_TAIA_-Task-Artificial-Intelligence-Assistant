from datetime import datetime, timezone
from uuid import uuid4

from backend.app.modules.reminders.adapters.outbound.telegram_notification_sender import TelegramNotificationSender
from backend.app.modules.reminders.domain.entities import Notification, Reminder


class FakeBot:
    def __init__(self):
        self.calls = []

    def send_message(self, *, chat_id, text):
        self.calls.append((chat_id, text))


def test_telegram_sender_resolves_linked_user_and_sends():
    bot = FakeBot()
    user_id = uuid4()
    sender = TelegramNotificationSender(
        bot_client=bot,
        telegram_user_id_resolver=lambda current_user_id: 123456,
        reminder_user_id_resolver=lambda reminder_id: user_id,
    )

    notification = Notification(reminder_id=7, message='Entrega mañana', date_send=datetime.now(timezone.utc))
    assert sender.send(notification) is True
    assert bot.calls == [(123456, 'Entrega mañana')]


def test_telegram_sender_returns_false_when_user_has_no_telegram():
    bot = FakeBot()
    sender = TelegramNotificationSender(
        bot_client=bot,
        telegram_user_id_resolver=lambda current_user_id: None,
        reminder_user_id_resolver=lambda reminder_id: uuid4(),
    )

    assert sender.send(Notification(reminder_id=7, message='Aviso', date_send=datetime.now(timezone.utc))) is False
    assert bot.calls == []
