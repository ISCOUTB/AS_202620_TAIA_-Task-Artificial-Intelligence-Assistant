"""Repositorios de Reminders sobre la conexión compartida; los compone `main.py`."""

from app.modules.reminders.adapters.outbound.sqlalchemy_reminder_repository import (
    SQLAlchemyNotificationRepository,
    SQLAlchemyReminderRepository,
)
from app.shared.adapters.outbound.database import get_session_factory


def get_reminder_repository() -> SQLAlchemyReminderRepository:
    return SQLAlchemyReminderRepository(get_session_factory())


def get_notification_repository() -> SQLAlchemyNotificationRepository:
    return SQLAlchemyNotificationRepository(get_session_factory())
