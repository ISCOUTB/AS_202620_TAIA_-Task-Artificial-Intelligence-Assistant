"""Integration coverage for adapters that replaced process-memory storage."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.modules.ai.adapters.outbound.sqlalchemy_conversation_store import SqlAlchemyConversationStore
from app.modules.ai.domain.conversation import Conversation
from app.modules.ai.domain.messages import ActionKind, ExtractedTaskData, PendingAction
from app.modules.reminders.adapters.outbound.sqlalchemy_reminder_repository import SQLAlchemyReminderRepository
from app.modules.reminders.domain.entities import Notification, Reminder
from app.modules.usuario.adapters.outbound.sqlalchemy_telegram_link_repository import SqlAlchemyTelegramLinkRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import UserModel
from app.modules.usuario.application.ports.outbound.telegram_link_repository import TelegramLinkToken


def test_telegram_link_token_round_trip_uses_hash(clean_db):
    user_id = uuid.uuid4()
    with clean_db.begin() as session:
        session.add(UserModel(id=user_id, full_name="Ana", email=f"{user_id}@example.com", password_hash="h"))

    repository = SqlAlchemyTelegramLinkRepository(clean_db)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    repository.save(TelegramLinkToken(token="secret-code", user_id=user_id, expires_at=expires_at))

    stored = repository.get("secret-code")
    assert stored is not None and stored.user_id == user_id and stored.used is False
    with clean_db() as session:
        code_hash = session.scalar(text("SELECT code_hash FROM telegram_link_codes"))
    assert code_hash == hashlib.sha256(b"secret-code").hexdigest()

    repository.mark_used("secret-code")
    assert repository.get("secret-code").used is True


def test_reminders_and_notifications_round_trip(clean_db):
    repository = SQLAlchemyReminderRepository(clean_db)
    reminder = Reminder(
        id=repository.next_id(),
        user_id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        message="Entregar informe",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    repository.create(reminder)
    assert repository.get_by_id(reminder.id).message == "Entregar informe"
    assert repository.list_by_user(reminder.user_id)[0].id == reminder.id

    repository.update(reminder.mark_completed())
    assert repository.get_by_id(reminder.id).is_completed is True

    notification = Notification(
        reminder_id=reminder.id,
        message=reminder.message,
        date_send=datetime.now(timezone.utc),
    )
    repository.create_notification(notification)
    repository.record_notification_attempt(notification, sent=True)
    with clean_db() as session:
        assert session.scalar(text("SELECT count(*) FROM notifications")) == 1
        assert session.scalar(text("SELECT status FROM reminders")) == "sent"
        assert session.scalar(text("SELECT push_attempts FROM notifications")) == 1

    with pytest.raises(ValueError, match="enviado"):
        repository.delete(reminder.id)


def test_conversation_and_pending_action_round_trip(clean_db):
    store = SqlAlchemyConversationStore(clean_db)
    user_id = str(uuid.uuid4())
    conversation = Conversation(user_id=user_id)
    conversation.record("user", "Crea una tarea")
    conversation.set_pending(
        PendingAction(
            kind=ActionKind.CREATE_TASK,
            task=ExtractedTaskData(
                title="Informe",
                due_at=datetime.now(timezone.utc) + timedelta(days=2),
            ),
            summary="¿Confirmas?",
        )
    )
    store.save(conversation)

    restored = store.get(user_id)
    assert restored.turns[0].text == "Crea una tarea"
    assert restored.pending is not None
    assert restored.pending.task.title == "Informe"
