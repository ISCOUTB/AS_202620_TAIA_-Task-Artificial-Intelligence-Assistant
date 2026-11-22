"""Persistencia de `reminders` y `notifications` en PostgreSQL (diccionario §7, RF-REC-05, RF-NOT-02…04)."""

import os
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.modules.reminders.adapters.outbound.sqlalchemy_reminder_repository import (
    SQLAlchemyNotificationRepository,
    SQLAlchemyReminderRepository,
)
from app.modules.reminders.application.use_cases.dispatch_due_reminders import DispatchDueRemindersUseCase
from app.modules.reminders.domain.entities import Notification, Reminder, ReminderOrigin, ReminderStatus
from app.shared.clock import BOGOTA_TZ
from tests.test_reminders_doubles import FakeDevices, FakePush, FakeTasks

USER = uuid.uuid4()
OTHER = uuid.uuid4()
SIX_PM = datetime(2026, 10, 7, 18, 0, tzinfo=BOGOTA_TZ)


@pytest.fixture
def repos(clean_db):
    return SQLAlchemyReminderRepository(clean_db), SQLAlchemyNotificationRepository(clean_db)


def _reminder(user=USER, task=None, moment=SIX_PM, origin=ReminderOrigin.AUTOMATIC, message=None) -> Reminder:
    return Reminder(id=uuid.uuid4(), user_id=user, task_id=task or uuid.uuid4(), scheduled_at=moment,
                    origin=origin, custom_message=message)


def _notification(reminder: Reminder, created_at=SIX_PM) -> Notification:
    return Notification(id=uuid.uuid4(), reminder_id=reminder.id, message="Recuerda", created_at=created_at)


def test_round_trip_follows_the_dictionary(repos, clean_db):
    reminders, _ = repos
    reminder = _reminder(moment=SIX_PM.astimezone(timezone.utc), message="Mío")

    reminders.add_all([reminder])

    stored = reminders.get(reminder.id)
    assert stored.scheduled_at == SIX_PM and stored.scheduled_at.tzinfo == BOGOTA_TZ
    assert (stored.origin, stored.status, stored.custom_message) == (
        ReminderOrigin.AUTOMATIC, ReminderStatus.PENDING, "Mío")
    with clean_db() as session:
        row = session.execute(text("SELECT origin::text, status::text FROM reminders")).one()
    assert tuple(row) == ("automatic", "pending")


def test_lists_are_ordered_by_scheduled_at(repos):
    reminders, _ = repos
    task = uuid.uuid4()
    late, early = _reminder(task=task, moment=SIX_PM), _reminder(task=task, moment=SIX_PM - timedelta(days=1))
    reminders.add_all([late, early, _reminder(user=OTHER)])

    assert [r.id for r in reminders.list_by_task(task)] == [early.id, late.id]
    assert [r.id for r in reminders.list_by_user(USER)] == [early.id, late.id]


def test_update_only_while_pending_rf_rec_04(repos):
    reminders, _ = repos
    reminder = _reminder()
    reminders.add_all([reminder])
    edited = replace(reminder, custom_message="Nuevo", origin=ReminderOrigin.CUSTOM)

    assert reminders.update_pending(edited) is True
    assert reminders.get(reminder.id).origin is ReminderOrigin.CUSTOM
    reminders.claim(reminder.id, _notification(reminder))
    assert reminders.update_pending(edited) is False


def test_sent_reminder_is_kept_rf_rec_05(repos):
    reminders, _ = repos
    sent, cancelled = _reminder(), _reminder()
    reminders.add_all([sent, cancelled])
    reminders.claim(sent.id, _notification(sent))
    reminders.cancel([cancelled.id])

    assert reminders.delete_unsent(sent.id) is False
    assert reminders.delete_unsent(cancelled.id) is True
    assert reminders.get(sent.id) is not None and reminders.get(cancelled.id) is None


def test_cancel_only_touches_pending(repos):
    reminders, _ = repos
    pending, sent, foreign = _reminder(), _reminder(), _reminder(user=OTHER)
    reminders.add_all([pending, sent, foreign])
    reminders.claim(sent.id, _notification(sent))

    reminders.cancel_pending_for_user(USER)

    assert reminders.get(pending.id).status is ReminderStatus.CANCELLED
    assert reminders.get(sent.id).status is ReminderStatus.SENT
    assert reminders.get(foreign.id).status is ReminderStatus.PENDING


def test_replace_automatic_keeps_sent_and_custom_rf_rec_06(repos):
    reminders, _ = repos
    task = uuid.uuid4()
    sent, pending, custom = _reminder(task=task), _reminder(task=task), _reminder(task=task, origin=ReminderOrigin.CUSTOM)
    reminders.add_all([sent, pending, custom])
    reminders.claim(sent.id, _notification(sent))
    new = _reminder(task=task, moment=SIX_PM + timedelta(days=1))

    reminders.replace_automatic(task, [new])

    assert {r.id for r in reminders.list_by_task(task)} == {sent.id, custom.id, new.id}


def test_claim_is_conditional_rf_not_02(repos, clean_db):
    reminders, _ = repos
    reminder = _reminder()
    reminders.add_all([reminder])

    assert reminders.claim(reminder.id, _notification(reminder)) is True
    assert reminders.claim(reminder.id, _notification(reminder)) is False
    with clean_db() as session:
        assert session.scalar(text("SELECT count(*) FROM notifications")) == 1


def _dispatcher(clean_db_or_factory, push):
    tasks, devices = FakeTasks(), FakeDevices()
    return tasks, devices, DispatchDueRemindersUseCase(
        SQLAlchemyReminderRepository(clean_db_or_factory), SQLAlchemyNotificationRepository(clean_db_or_factory),
        tasks, devices, push, sleep=lambda _: None)


def test_running_twice_sends_a_single_notification_rf_not_02(clean_db):
    push = FakePush()
    tasks, devices, dispatch = _dispatcher(clean_db, push)
    task = tasks.add(USER, due_at=SIX_PM + timedelta(days=1))
    devices.tokens[USER] = ["token-a"]
    SQLAlchemyReminderRepository(clean_db).add_all([_reminder(task=task.task_id)])

    first = dispatch.execute(SIX_PM)
    second = dispatch.execute(SIX_PM)

    assert (first, second) == (1, 0)
    assert len(push.sent) == 1
    with clean_db() as session:
        row = session.execute(text("SELECT count(*), max(push_attempts) FROM notifications")).one()
        assert tuple(row) == (1, 1)
        assert session.scalar(text("SELECT status::text FROM reminders")) == "sent"


@pytest.fixture
def tokyo_session_factory(clean_db):
    """Sesiones con la zona de PostgreSQL en Asia/Tokyo: simula un servidor en otra zona (RT-03)."""

    engine = create_engine(os.environ["TEST_DATABASE_URL"], connect_args={"options": "-c timezone=Asia/Tokyo"})
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.mark.parametrize("now_zone", [timezone.utc, timezone(timedelta(hours=9))])
def test_six_pm_colombia_reminder_goes_out_in_the_six_pm_run_rf_not_02_rt_03(tokyo_session_factory, now_zone):
    push = FakePush()
    tasks, devices, dispatch = _dispatcher(tokyo_session_factory, push)
    task = tasks.add(USER, due_at=SIX_PM + timedelta(days=1))
    devices.tokens[USER] = ["token-a"]
    SQLAlchemyReminderRepository(tokyo_session_factory).add_all([_reminder(task=task.task_id)])

    before = dispatch.execute((SIX_PM - timedelta(minutes=1)).astimezone(now_zone))
    on_time = dispatch.execute(SIX_PM.astimezone(now_zone))

    assert (before, on_time) == (0, 1)
    assert len(push.sent) == 1


def _sent_with_notification(reminders, user=USER, created_at=SIX_PM) -> Notification:
    reminder = _reminder(user=user)
    reminders.add_all([reminder])
    notification = _notification(reminder, created_at)
    reminders.claim(reminder.id, notification)
    return notification


def test_inbox_lists_newest_first_with_pagination_rf_not_03(repos):
    reminders, notifications = repos
    old = _sent_with_notification(reminders, created_at=SIX_PM - timedelta(days=1))
    new = _sent_with_notification(reminders)
    _sent_with_notification(reminders, user=OTHER)

    page, total = notifications.list_for_user(USER, limit=1, offset=0)
    second, _ = notifications.list_for_user(USER, limit=1, offset=1)

    assert total == 2
    assert [n.id for n in page + second] == [new.id, old.id]


def test_inbox_read_state_rf_not_03(repos):
    reminders, notifications = repos
    first = _sent_with_notification(reminders)
    _sent_with_notification(reminders)
    foreign = _sent_with_notification(reminders, user=OTHER)

    read = notifications.mark_read(first.id, USER, SIX_PM)
    again = notifications.mark_read(first.id, USER, SIX_PM + timedelta(hours=1))

    assert read.read and again.read_at == SIX_PM
    assert notifications.mark_read(foreign.id, USER, SIX_PM) is None
    assert notifications.count_unread(USER) == 1
    notifications.mark_all_read(USER, SIX_PM)
    assert notifications.count_unread(USER) == 0
    assert notifications.count_unread(OTHER) == 1


def test_record_push_rf_not_02(repos):
    reminders, notifications = repos
    notification = _sent_with_notification(reminders)

    notifications.record_push(notification.id, 2, SIX_PM)

    [stored], _ = notifications.list_for_user(USER, 10, 0)
    assert (stored.push_attempts, stored.push_sent_at) == (2, SIX_PM)
