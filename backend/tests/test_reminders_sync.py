"""RF-REC-06, RF-TAR-02, RF-TAR-05, RF-TAR-08 y RF-USR-09 (lado Reminders) con dobles en memoria."""

import uuid
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from app.modules.reminders.application.errors import InvalidReminderError
from app.modules.reminders.application.ports.inbound.task_reminder_sync import ReminderPlan
from app.modules.reminders.application.services.task_reminder_sync import TaskReminderSyncService
from app.modules.reminders.domain.entities import Notification, Reminder, ReminderOrigin, ReminderStatus
from app.shared.clock import BOGOTA_TZ
from tests.test_reminders_doubles import NOW, FakeTasks, FixedClock, repository

USER = uuid.uuid4()
DUE = datetime(2026, 10, 8, 23, 59, tzinfo=BOGOTA_TZ)


def at(day: int, hour: int = 18) -> datetime:
    return datetime(2026, 10, day, hour, 0, tzinfo=BOGOTA_TZ)


@pytest.fixture
def env():
    repo, tasks, clock = repository(), FakeTasks(), FixedClock()
    task = tasks.add(USER, due_at=DUE)
    return repo, tasks, clock, task, TaskReminderSyncService(repo, tasks, clock)


def _by_origin(repo, task_id, origin):
    return [r for r in repo.list_by_task(task_id) if r.origin is origin]


def test_plan_none_creates_nothing_rf_tar_02(env):
    repo, _, _, task, sync = env

    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="none"))

    assert repo.list_by_task(task.task_id) == []


def test_plan_default_applies_policy_in_same_operation_rf_tar_02_rf_rec_02(env):
    repo, _, _, task, sync = env

    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))

    reminders = repo.list_by_task(task.task_id)
    assert [r.scheduled_at for r in reminders] == [at(2), at(4), at(6), at(7)]
    assert {(r.origin, r.status, r.user_id) for r in reminders} == {
        (ReminderOrigin.AUTOMATIC, ReminderStatus.PENDING, USER)}


def test_plan_custom_uses_given_dates_rf_tar_02(env):
    repo, _, _, task, sync = env
    plan = ReminderPlan(mode="custom", custom_at=(at(5, 9), at(3, 9), at(3, 9)))

    sync.on_task_created(USER, task.task_id, DUE, plan)

    reminders = repo.list_by_task(task.task_id)
    assert [r.scheduled_at for r in reminders] == [at(3, 9), at(5, 9)]
    assert all(r.origin is ReminderOrigin.CUSTOM for r in reminders)


@pytest.mark.parametrize("moment", [NOW - timedelta(hours=1), DUE + timedelta(hours=1)])
def test_plan_custom_applies_rf_rec_01_rules_and_saves_nothing(env, moment):
    repo, _, _, task, sync = env
    plan = ReminderPlan(mode="custom", custom_at=(at(3), moment))

    with pytest.raises(InvalidReminderError):
        sync.on_task_created(USER, task.task_id, DUE, plan)
    assert repo.list_by_task(task.task_id) == []


def test_plan_custom_without_dates_is_invalid_rf_tar_02(env):
    _, _, _, task, sync = env

    with pytest.raises(InvalidReminderError):
        sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="custom"))


def _custom(repo, task_id, moment, status=ReminderStatus.PENDING) -> Reminder:
    reminder = Reminder(id=uuid.uuid4(), user_id=USER, task_id=task_id, scheduled_at=moment,
                        origin=ReminderOrigin.CUSTOM, status=status)
    repo.add_all([reminder])
    return reminder


def test_due_change_recalculates_automatic_rf_rec_06_rf_tar_06(env):
    repo, _, _, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    keep = _custom(repo, task.task_id, at(3, 9))

    sync.on_due_changed(USER, task.task_id, datetime(2026, 10, 5, 12, 0, tzinfo=BOGOTA_TZ))

    automatic = _by_origin(repo, task.task_id, ReminderOrigin.AUTOMATIC)
    assert [r.scheduled_at for r in automatic] == [at(1), at(3), at(4)]
    assert repo.get(keep.id) == keep


def test_due_change_cancels_custom_after_new_due_rf_rec_06(env):
    repo, _, _, task, sync = env
    before = _custom(repo, task.task_id, at(3, 9))
    after = _custom(repo, task.task_id, at(6, 9))

    sync.on_due_changed(USER, task.task_id, at(5, 12))

    assert repo.get(before.id).status is ReminderStatus.PENDING
    assert repo.get(after.id).status is ReminderStatus.CANCELLED
    assert _by_origin(repo, task.task_id, ReminderOrigin.AUTOMATIC) == []


def test_due_change_keeps_sent_automatic_rf_rec_06(env):
    repo, _, clock, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    first = repo.list_by_task(task.task_id)[0]
    repo.claim(first.id, _notification(first))
    clock.now = at(3)

    sync.on_due_changed(USER, task.task_id, datetime(2026, 10, 10, 23, 59, tzinfo=BOGOTA_TZ))

    automatic = _by_origin(repo, task.task_id, ReminderOrigin.AUTOMATIC)
    assert [r.scheduled_at for r in automatic] == [at(2), at(4), at(6), at(8), at(9)]
    assert repo.get(first.id).status is ReminderStatus.SENT


def test_closing_cancels_pending_rf_rec_06_rf_tar_07_rf_tar_10(env):
    repo, _, _, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    custom = _custom(repo, task.task_id, at(3, 9))

    sync.on_task_closed(USER, task.task_id)

    assert {r.status for r in repo.list_by_task(task.task_id)} == {ReminderStatus.CANCELLED}
    assert repo.get(custom.id).status is ReminderStatus.CANCELLED


def test_reopen_regenerates_future_automatic_rf_tar_08(env):
    repo, _, clock, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    sync.on_task_closed(USER, task.task_id)
    clock.now = at(5, 10)

    sync.on_task_reopened(USER, task.task_id, DUE)

    reminders = repo.list_by_task(task.task_id)
    assert [(r.scheduled_at, r.status) for r in reminders] == [
        (at(6), ReminderStatus.PENDING), (at(7), ReminderStatus.PENDING)]


def test_reopen_without_automatic_creates_nothing_rf_tar_08(env):
    repo, _, _, task, sync = env
    custom = _custom(repo, task.task_id, at(3, 9), status=ReminderStatus.CANCELLED)

    sync.on_task_reopened(USER, task.task_id, DUE)

    assert repo.list_by_task(task.task_id) == [custom]


def test_reopen_after_due_creates_nothing_rf_tar_08(env):
    repo, _, clock, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    sync.on_task_closed(USER, task.task_id)
    clock.now = DUE + timedelta(hours=1)

    sync.on_task_reopened(USER, task.task_id, DUE)

    assert repo.list_by_task(task.task_id) == []


def test_deactivated_account_cancels_all_pending_rf_usr_09(env):
    repo, tasks, _, task, sync = env
    other_task = tasks.add(USER, due_at=DUE)
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    sync.on_task_created(USER, other_task.task_id, DUE, ReminderPlan(mode="default"))
    stranger = Reminder(id=uuid.uuid4(), user_id=uuid.uuid4(), task_id=uuid.uuid4(), scheduled_at=at(3),
                        origin=ReminderOrigin.CUSTOM)
    repo.add_all([stranger])

    sync.cancel_all_for_user(USER)

    assert {r.status for r in repo.list_by_user(USER)} == {ReminderStatus.CANCELLED}
    assert repo.get(stranger.id).status is ReminderStatus.PENDING


def test_list_for_task_is_ordered_and_has_messages_rf_tar_05(env):
    repo, _, _, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))
    custom = _custom(repo, task.task_id, at(3, 9))
    repo.reminders[custom.id] = replace(custom, custom_message="Mío")

    views = sync.list_for_task(USER, task.task_id)

    assert [v.scheduled_at for v in views] == [at(2), at(3, 9), at(4), at(6), at(7)]
    assert views[1].message == "Mío"
    assert views[0].message == "Recuerda: Informe (Cálculo) vence el 08/10/2026 23:59"
    assert (views[0].origin, views[0].status) == ("automatic", "pending")


def test_list_for_task_of_another_user_is_empty_rf_tar_05_rt_02(env):
    _, _, _, task, sync = env
    sync.on_task_created(USER, task.task_id, DUE, ReminderPlan(mode="default"))

    assert sync.list_for_task(uuid.uuid4(), task.task_id) == []


def _notification(reminder):
    return Notification(id=uuid.uuid4(), reminder_id=reminder.id, message="x", created_at=NOW)
