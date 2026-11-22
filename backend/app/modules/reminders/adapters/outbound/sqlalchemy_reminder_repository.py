"""Persistencia en PostgreSQL de `reminders` y `notifications` (diccionario de datos §7)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import sessionmaker

from app.modules.reminders.adapters.outbound.sqlalchemy_models import NotificationModel, ReminderModel
from app.modules.reminders.application.ports.outbound.reminder_repository import (
    NotificationRepository,
    ReminderRepository,
)
from app.modules.reminders.domain.entities import (
    Notification,
    Reminder,
    ReminderOrigin,
    ReminderStatus,
)
from app.shared.clock import as_bogota

PENDING = ReminderStatus.PENDING.value
SENT = ReminderStatus.SENT.value


class SQLAlchemyReminderRepository(ReminderRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add_all(self, reminders: list[Reminder]) -> None:
        with self._session_factory.begin() as session:
            session.add_all([_reminder_to_model(r) for r in reminders])

    def get(self, reminder_id: UUID) -> Reminder | None:
        with self._session_factory() as session:
            model = session.get(ReminderModel, reminder_id)
            return _reminder_to_domain(model) if model is not None else None

    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        return self._list(ReminderModel.user_id == user_id)

    def list_by_task(self, task_id: UUID) -> list[Reminder]:
        return self._list(ReminderModel.task_id == task_id)

    def update_pending(self, reminder: Reminder) -> bool:
        statement = (
            update(ReminderModel)
            .where(ReminderModel.id == reminder.id, ReminderModel.status == PENDING)
            .values(
                scheduled_at=reminder.scheduled_at,
                custom_message=reminder.custom_message,
                origin=reminder.origin.value,
            )
        )
        with self._session_factory.begin() as session:
            return session.execute(statement).rowcount == 1

    def delete_unsent(self, reminder_id: UUID) -> bool:
        with self._session_factory.begin() as session:
            model = session.get(ReminderModel, reminder_id, with_for_update=True)
            if model is not None and model.status == SENT:
                return False
            session.execute(delete(ReminderModel).where(ReminderModel.id == reminder_id))
            return True

    def cancel(self, reminder_ids: list[UUID]) -> int:
        if not reminder_ids:
            return 0
        return self._cancel_where(ReminderModel.id.in_(reminder_ids))

    def cancel_pending_for_user(self, user_id: UUID) -> None:
        self._cancel_where(ReminderModel.user_id == user_id)

    def replace_automatic(self, task_id: UUID, reminders: list[Reminder]) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                delete(ReminderModel).where(
                    ReminderModel.task_id == task_id,
                    ReminderModel.origin == ReminderOrigin.AUTOMATIC.value,
                    ReminderModel.status != SENT,
                )
            )
            session.add_all([_reminder_to_model(r) for r in reminders])

    def list_due(self, now: datetime) -> list[Reminder]:
        # timestamptz contra un instante con zona: no depende de la zona del servidor (RT-03).
        return self._list(ReminderModel.status == PENDING, ReminderModel.scheduled_at <= now)

    def claim(self, reminder_id: UUID, notification: Notification) -> bool:
        claimed = (
            update(ReminderModel)
            .where(ReminderModel.id == reminder_id, ReminderModel.status == PENDING)
            .values(status=SENT)
        )
        with self._session_factory.begin() as session:
            if session.execute(claimed).rowcount != 1:
                return False
            session.add(_notification_to_model(notification))
            return True

    def _list(self, *conditions) -> list[Reminder]:
        query = select(ReminderModel).where(*conditions).order_by(ReminderModel.scheduled_at, ReminderModel.id)
        with self._session_factory() as session:
            return [_reminder_to_domain(model) for model in session.scalars(query)]

    def _cancel_where(self, condition) -> int:
        statement = (
            update(ReminderModel)
            .where(condition, ReminderModel.status == PENDING)
            .values(status=ReminderStatus.CANCELLED.value)
        )
        with self._session_factory.begin() as session:
            return session.execute(statement).rowcount


class SQLAlchemyNotificationRepository(NotificationRepository):
    """El usuario de una notificación se obtiene a través de su recordatorio."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> tuple[list[Notification], int]:
        owned = _owned_by(user_id)
        page = owned.order_by(NotificationModel.created_at.desc(), NotificationModel.id.desc())
        with self._session_factory() as session:
            total = session.scalar(select(func.count()).select_from(owned.subquery()))
            items = session.scalars(page.limit(limit).offset(offset))
            return [_notification_to_domain(model) for model in items], total

    def mark_read(self, notification_id: UUID, user_id: UUID, now: datetime) -> Notification | None:
        with self._session_factory.begin() as session:
            model = session.scalars(_owned_by(user_id).where(NotificationModel.id == notification_id)).first()
            if model is None:
                return None
            if model.read_at is None:
                model.read_at = now
            return _notification_to_domain(model)

    def mark_all_read(self, user_id: UUID, now: datetime) -> None:
        statement = (
            update(NotificationModel)
            .where(NotificationModel.read_at.is_(None), NotificationModel.reminder_id.in_(_user_reminders(user_id)))
            .values(read_at=now)
        )
        with self._session_factory.begin() as session:
            session.execute(statement)

    def count_unread(self, user_id: UUID) -> int:
        unread = _owned_by(user_id).where(NotificationModel.read_at.is_(None))
        with self._session_factory() as session:
            return session.scalar(select(func.count()).select_from(unread.subquery()))

    def record_push(self, notification_id: UUID, attempts: int, sent_at: datetime | None) -> None:
        statement = (
            update(NotificationModel)
            .where(NotificationModel.id == notification_id)
            .values(push_attempts=attempts, push_sent_at=sent_at)
        )
        with self._session_factory.begin() as session:
            session.execute(statement)


def _user_reminders(user_id: UUID):
    return select(ReminderModel.id).where(ReminderModel.user_id == user_id)


def _owned_by(user_id: UUID):
    return select(NotificationModel).where(NotificationModel.reminder_id.in_(_user_reminders(user_id)))


def _reminder_to_model(reminder: Reminder) -> ReminderModel:
    return ReminderModel(
        id=reminder.id,
        user_id=reminder.user_id,
        task_id=reminder.task_id,
        scheduled_at=reminder.scheduled_at,
        custom_message=reminder.custom_message,
        origin=reminder.origin.value,
        status=reminder.status.value,
    )


def _reminder_to_domain(model: ReminderModel) -> Reminder:
    return Reminder(
        id=model.id,
        user_id=model.user_id,
        task_id=model.task_id,
        scheduled_at=as_bogota(model.scheduled_at),
        custom_message=model.custom_message,
        origin=ReminderOrigin(model.origin),
        status=ReminderStatus(model.status),
    )


def _notification_to_model(notification: Notification) -> NotificationModel:
    return NotificationModel(
        id=notification.id,
        reminder_id=notification.reminder_id,
        message=notification.message,
        created_at=notification.created_at,
        push_attempts=notification.push_attempts,
        push_sent_at=notification.push_sent_at,
        read_at=notification.read_at,
    )


def _notification_to_domain(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        reminder_id=model.reminder_id,
        message=model.message,
        created_at=as_bogota(model.created_at),
        push_attempts=model.push_attempts,
        push_sent_at=as_bogota(model.push_sent_at) if model.push_sent_at else None,
        read_at=as_bogota(model.read_at) if model.read_at else None,
    )
