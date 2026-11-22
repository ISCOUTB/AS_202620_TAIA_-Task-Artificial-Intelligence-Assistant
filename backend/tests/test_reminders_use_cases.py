"""RF-REC-01, RF-REC-04 y RF-REC-05 con repositorio en memoria y dobles de Academic."""

import uuid
from dataclasses import replace
from datetime import timedelta, timezone

import pytest

from app.modules.reminders.application.errors import (
    InvalidReminderError,
    ReminderNotFoundError,
    ReminderStateError,
    ReminderTaskNotFoundError,
)
from app.modules.reminders.application.use_cases.create_reminder import CreateReminderUseCase
from app.modules.reminders.application.use_cases.delete_reminder import DeleteReminderUseCase
from app.modules.reminders.application.use_cases.edit_reminder import EditReminderUseCase
from app.modules.reminders.domain.entities import (
    Reminder,
    ReminderOrigin,
    ReminderStatus,
    default_message,
)
from tests.test_reminders_doubles import NOW, FakeTasks, FixedClock, repository

USER = uuid.uuid4()
OTHER = uuid.uuid4()


@pytest.fixture
def setup():
    repo, tasks = repository(), FakeTasks()
    create = CreateReminderUseCase(repo, tasks, FixedClock())
    edit = EditReminderUseCase(repo, tasks, FixedClock())
    delete = DeleteReminderUseCase(repo)
    return repo, tasks, create, edit, delete


def test_create_custom_reminder_rf_rec_01(setup):
    repo, tasks, create, _, _ = setup
    task = tasks.add(USER)

    reminder = create.execute(USER, task.task_id, NOW + timedelta(days=1), "  Repasar  ")

    assert reminder.origin is ReminderOrigin.CUSTOM
    assert reminder.status is ReminderStatus.PENDING
    assert reminder.custom_message == "Repasar"
    assert repo.get(reminder.id) == reminder


def test_message_is_optional_rf_rec_01(setup):
    _, tasks, create, _, _ = setup
    task = tasks.add(USER)

    reminder = create.execute(USER, task.task_id, NOW + timedelta(days=1), None)

    assert reminder.custom_message is None


def test_default_message_in_colombian_time_rf_rec_01_rt_03():
    due_utc = NOW.replace(day=8, hour=23, minute=59).astimezone(timezone.utc)

    message = default_message("Informe", "Cálculo", due_utc)

    assert message == "Recuerda: Informe (Cálculo) vence el 08/10/2026 23:59"


def test_naive_date_is_colombian_time_rf_rec_01_rt_03(setup):
    _, tasks, create, _, _ = setup
    task = tasks.add(USER)

    reminder = create.execute(USER, task.task_id, (NOW + timedelta(days=1)).replace(tzinfo=None), None)

    assert reminder.scheduled_at == NOW + timedelta(days=1)


@pytest.mark.parametrize("offset", [timedelta(0), -timedelta(minutes=1)])
def test_date_must_be_future_rf_rec_01(setup, offset):
    _, tasks, create, _, _ = setup
    task = tasks.add(USER)

    with pytest.raises(InvalidReminderError):
        create.execute(USER, task.task_id, NOW + offset, None)


@pytest.mark.parametrize("offset", [timedelta(0), timedelta(minutes=1)])
def test_date_must_be_before_due_rf_rec_01(setup, offset):
    _, tasks, create, _, _ = setup
    task = tasks.add(USER)

    with pytest.raises(InvalidReminderError):
        create.execute(USER, task.task_id, task.due_at + offset, None)


def test_task_must_be_own_rf_rec_01_rt_02(setup):
    _, tasks, create, _, _ = setup
    task = tasks.add(OTHER)

    with pytest.raises(ReminderTaskNotFoundError):
        create.execute(USER, task.task_id, NOW + timedelta(days=1), None)


def test_task_must_be_pending_rf_rec_01(setup):
    _, tasks, create, _, _ = setup
    task = tasks.add(USER, completed=True)

    with pytest.raises(ReminderStateError):
        create.execute(USER, task.task_id, NOW + timedelta(days=1), None)


def test_blank_message_is_invalid_rf_rec_01(setup):
    _, tasks, create, _, _ = setup
    task = tasks.add(USER)

    with pytest.raises(InvalidReminderError):
        create.execute(USER, task.task_id, NOW + timedelta(days=1), "   ")


def _stored(repo, tasks, origin=ReminderOrigin.AUTOMATIC, status=ReminderStatus.PENDING) -> Reminder:
    task = tasks.add(USER)
    reminder = Reminder(id=uuid.uuid4(), user_id=USER, task_id=task.task_id,
                        scheduled_at=NOW + timedelta(days=2), origin=origin, status=status)
    repo.add_all([reminder])
    return reminder


def test_edit_date_and_message_rf_rec_04(setup):
    repo, tasks, _, edit, _ = setup
    reminder = _stored(repo, tasks, origin=ReminderOrigin.CUSTOM)

    edited = edit.execute(reminder.id, USER, NOW + timedelta(days=3), "Nuevo")

    assert (edited.scheduled_at, edited.custom_message) == (NOW + timedelta(days=3), "Nuevo")
    assert repo.get(reminder.id) == edited


def test_edited_automatic_becomes_custom_rf_rec_04(setup):
    repo, tasks, _, edit, _ = setup
    reminder = _stored(repo, tasks)

    edited = edit.execute(reminder.id, USER, None, "Solo el mensaje")

    assert edited.origin is ReminderOrigin.CUSTOM
    assert edited.scheduled_at == reminder.scheduled_at


@pytest.mark.parametrize("status", [ReminderStatus.SENT, ReminderStatus.CANCELLED])
def test_only_pending_can_be_edited_rf_rec_04(setup, status):
    repo, tasks, _, edit, _ = setup
    reminder = _stored(repo, tasks, status=status)

    with pytest.raises(ReminderStateError):
        edit.execute(reminder.id, USER, None, "Cambio")


def test_edit_applies_rf_rec_01_rules_rf_rec_04(setup):
    repo, tasks, _, edit, _ = setup
    reminder = _stored(repo, tasks)
    due = tasks.get(reminder.task_id, USER).due_at

    with pytest.raises(InvalidReminderError):
        edit.execute(reminder.id, USER, due + timedelta(hours=1), None)


def test_edit_of_another_users_reminder_is_not_found_rf_rec_04_rt_02(setup):
    repo, tasks, _, edit, _ = setup
    reminder = _stored(repo, tasks)

    with pytest.raises(ReminderNotFoundError):
        edit.execute(reminder.id, OTHER, None, "Cambio")


def test_edit_loses_race_against_dispatch_rf_rec_04(setup):
    repo, tasks, _, edit, _ = setup
    reminder = _stored(repo, tasks)
    original_update = repo.update_pending

    def sent_meanwhile(changed):
        repo.reminders[reminder.id] = replace(reminder, status=ReminderStatus.SENT)
        return original_update(changed)

    repo.update_pending = sent_meanwhile

    with pytest.raises(ReminderStateError):
        edit.execute(reminder.id, USER, None, "Tarde")


@pytest.mark.parametrize("status", [ReminderStatus.PENDING, ReminderStatus.CANCELLED])
def test_delete_pending_or_cancelled_rf_rec_05(setup, status):
    repo, tasks, _, _, delete = setup
    reminder = _stored(repo, tasks, status=status)

    delete.execute(reminder.id, USER)

    assert repo.get(reminder.id) is None


def test_sent_reminder_is_not_deleted_rf_rec_05(setup):
    repo, tasks, _, _, delete = setup
    reminder = _stored(repo, tasks, status=ReminderStatus.SENT)

    with pytest.raises(ReminderStateError):
        delete.execute(reminder.id, USER)
    assert repo.get(reminder.id) == reminder


def test_delete_of_another_users_reminder_is_not_found_rf_rec_05_rt_02(setup):
    repo, tasks, _, _, delete = setup
    reminder = _stored(repo, tasks)

    with pytest.raises(ReminderNotFoundError):
        delete.execute(reminder.id, OTHER)
