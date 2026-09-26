"""SQLAlchemy persistence for reminders and their notifications."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from app.modules.reminders.adapters.outbound.sqlalchemy_models import NotificationModel, ReminderModel
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.domain.entities import Notification, Reminder
from app.shared.clock import as_bogota


class SQLAlchemyReminderRepository(ReminderRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def next_id(self) -> UUID:
        return uuid.uuid4()

    def create(self, reminder: Reminder) -> Reminder:
        with self._session_factory.begin() as session:
            session.add(_to_model(reminder))
        return reminder

    def get_by_id(self, reminder_id: UUID) -> Reminder | None:
        with self._session_factory() as session:
            model = session.get(ReminderModel, reminder_id)
            return _to_domain(model) if model is not None else None

    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        with self._session_factory() as session:
            models = session.scalars(
                select(ReminderModel)
                .where(ReminderModel.user_id == user_id)
                .order_by(ReminderModel.scheduled_at, ReminderModel.id)
            ).all()
            return [_to_domain(model) for model in models]

    def update(self, reminder: Reminder) -> Reminder:
        with self._session_factory.begin() as session:
            model = session.get(ReminderModel, reminder.id)
            if model is None:
                raise ValueError("Recordatorio no encontrado")
            model.custom_message = reminder.message
            model.scheduled_at = reminder.scheduled_at
            model.status = "cancelled" if reminder.is_completed else "pending"
        return reminder

    def delete(self, reminder_id: UUID) -> None:
        with self._session_factory.begin() as session:
            model = session.get(ReminderModel, reminder_id)
            if model is None:
                return
            if model.status == "sent":
                raise ValueError("Un recordatorio enviado no se puede eliminar")
            session.execute(delete(NotificationModel).where(NotificationModel.reminder_id == reminder_id))
            session.delete(model)

    def create_notification(self, notification: Notification) -> Notification:
        with self._session_factory.begin() as session:
            session.scalars(
                select(ReminderModel)
                .where(ReminderModel.id == notification.reminder_id)
                .with_for_update()
            ).one()
            existing = session.scalars(
                select(NotificationModel).where(NotificationModel.reminder_id == notification.reminder_id)
            ).first()
            if existing is None:
                session.add(
                    NotificationModel(
                        id=uuid.uuid4(),
                        reminder_id=notification.reminder_id,
                        message=notification.message,
                        created_at=notification.date_send,
                        read_at=notification.date_send if notification.read_status else None,
                    )
                )
                return notification
            return Notification(
                reminder_id=existing.reminder_id,
                message=existing.message,
                read_status=existing.read_at is not None,
                date_send=as_bogota(existing.created_at),
            )

    def record_notification_attempt(self, notification: Notification, sent: bool) -> None:
        with self._session_factory.begin() as session:
            model = session.scalars(
                select(NotificationModel).where(
                    NotificationModel.reminder_id == notification.reminder_id
                )
            ).first()
            if model is None:
                raise ValueError("Notificación no encontrada")
            model.push_attempts = min(model.push_attempts + 1, 4)
            if sent:
                model.push_sent_at = notification.date_send
                reminder = session.get(ReminderModel, notification.reminder_id)
                if reminder is not None:
                    reminder.status = "sent"


def _to_model(reminder: Reminder) -> ReminderModel:
    return ReminderModel(
        id=reminder.id,
        user_id=reminder.user_id,
        task_id=reminder.task_id,
        scheduled_at=reminder.scheduled_at,
        custom_message=reminder.message,
        origin="custom",
        status="cancelled" if reminder.is_completed else "pending",
    )


def _to_domain(model: ReminderModel) -> Reminder:
    return Reminder(
        id=model.id,
        user_id=model.user_id,
        message=model.custom_message or "Recordatorio de tarea",
        scheduled_at=as_bogota(model.scheduled_at),
        is_completed=model.status != "pending",
        task_id=model.task_id,
    )
