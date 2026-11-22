"""RF-NOT-02 y RF-NOT-04 · Envío de recordatorios vencidos, con dobles en memoria (ADR-0012)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.reminders.application.use_cases.dispatch_due_reminders import DispatchDueRemindersUseCase
from app.modules.reminders.domain.entities import Reminder, ReminderOrigin, ReminderStatus
from app.shared.clock import BOGOTA_TZ
from tests.test_reminders_doubles import FakeDevices, FakePush, FakeTasks, repository

USER = uuid.uuid4()
SIX_PM = datetime(2026, 10, 7, 18, 0, tzinfo=BOGOTA_TZ)
DUE = datetime(2026, 10, 8, 23, 59, tzinfo=BOGOTA_TZ)


class Env:
    def __init__(self, push: FakePush | None) -> None:
        self.repo, self.tasks, self.devices, self.push = repository(), FakeTasks(), FakeDevices(), push
        self.sleeps: list[float] = []
        self.task = self.tasks.add(USER, due_at=DUE)
        self.devices.tokens[USER] = ["token-a"]
        self.use_case = DispatchDueRemindersUseCase(
            self.repo, self.repo, self.tasks, self.devices, push, sleep=self.sleeps.append)

    def reminder(self, moment: datetime = SIX_PM, message: str | None = None) -> Reminder:
        reminder = Reminder(id=uuid.uuid4(), user_id=USER, task_id=self.task.task_id, scheduled_at=moment,
                            origin=ReminderOrigin.AUTOMATIC, custom_message=message)
        self.repo.add_all([reminder])
        return reminder

    def notifications(self):
        return list(self.repo.notifications.values())


@pytest.fixture
def env():
    return Env(FakePush())


def test_due_reminder_is_sent_and_saved_rf_not_02(env):
    reminder = env.reminder()

    assert env.use_case.execute(SIX_PM) == 1

    assert env.repo.get(reminder.id).status is ReminderStatus.SENT
    [notification] = env.notifications()
    assert notification.message == "Recuerda: Informe (Cálculo) vence el 08/10/2026 23:59"
    assert (notification.push_attempts, notification.push_sent_at) == (1, SIX_PM)
    assert env.push.sent == [("token-a", notification.message)]


def test_custom_message_is_copied_rf_not_02(env):
    env.reminder(message="Llevar calculadora")

    env.use_case.execute(SIX_PM)

    assert env.notifications()[0].message == "Llevar calculadora"


def test_running_twice_sends_one_notification_rf_not_02(env):
    env.reminder()

    env.use_case.execute(SIX_PM)
    env.use_case.execute(SIX_PM + timedelta(minutes=1))

    assert len(env.notifications()) == 1
    assert len(env.push.sent) == 1


def test_future_reminder_waits_rf_not_02(env):
    reminder = env.reminder()

    assert env.use_case.execute(SIX_PM - timedelta(minutes=1)) == 0

    assert env.repo.get(reminder.id).status is ReminderStatus.PENDING


@pytest.mark.parametrize("now", [
    SIX_PM.astimezone(timezone.utc),
    SIX_PM.astimezone(timezone(timedelta(hours=9))),
])
def test_compares_instants_not_server_time_rf_not_02_rt_03(env, now):
    env.reminder()

    assert env.use_case.execute(now) == 1


@pytest.mark.parametrize("close", ["complete", "delete"])
def test_closed_task_is_not_notified_and_reminder_cancelled_rf_not_02_rf_tar_10(env, close):
    reminder = env.reminder()
    getattr(env.tasks, close)(USER, env.task.task_id)

    assert env.use_case.execute(SIX_PM) == 0

    assert env.repo.get(reminder.id).status is ReminderStatus.CANCELLED
    assert env.notifications() == [] and env.push.calls == []


def test_inactive_account_is_not_notified_rf_not_02_rf_usr_09(env):
    reminder = env.reminder()
    env.devices.inactive.add(USER)

    assert env.use_case.execute(SIX_PM) == 0

    assert env.repo.get(reminder.id).status is ReminderStatus.CANCELLED
    assert env.notifications() == []


def test_without_devices_saves_notification_and_marks_sent_rf_not_04(env):
    reminder = env.reminder()
    env.devices.tokens[USER] = []

    assert env.use_case.execute(SIX_PM) == 1

    assert env.repo.get(reminder.id).status is ReminderStatus.SENT
    [notification] = env.notifications()
    assert (notification.push_attempts, notification.push_sent_at) == (0, None)


def test_without_fcm_configured_behaves_like_rf_not_04():
    env = Env(push=None)
    env.reminder()

    assert env.use_case.execute(SIX_PM) == 1

    assert env.notifications()[0].push_attempts == 0


def test_sends_to_every_device_rf_not_02(env):
    env.devices.tokens[USER] = ["token-a", "token-b"]
    env.reminder()

    env.use_case.execute(SIX_PM)

    assert sorted(token for token, _ in env.push.sent) == ["token-a", "token-b"]


def test_retries_up_to_3_times_with_growing_wait_rf_not_02():
    env = Env(FakePush(failures={"token-a": 2}))
    env.reminder()

    env.use_case.execute(SIX_PM)

    assert env.sleeps == [1.0, 2.0]
    notification = env.notifications()[0]
    assert (notification.push_attempts, notification.push_sent_at) == (3, SIX_PM)


def test_gives_up_after_3_retries_rf_not_02():
    env = Env(FakePush(failures={"token-a": 10}))
    reminder = env.reminder()

    env.use_case.execute(SIX_PM)

    assert env.sleeps == [1.0, 2.0, 4.0]
    notification = env.notifications()[0]
    assert (notification.push_attempts, notification.push_sent_at) == (4, None)
    assert env.repo.get(reminder.id).status is ReminderStatus.SENT


def test_retries_only_failed_tokens_rf_not_02():
    env = Env(FakePush(failures={"token-b": 1}))
    env.devices.tokens[USER] = ["token-a", "token-b"]
    env.reminder()

    env.use_case.execute(SIX_PM)

    assert env.push.calls == ["token-a", "token-b", "token-b"]


def test_invalid_token_is_removed_rf_not_02():
    env = Env(FakePush(invalid={"token-a"}))
    env.reminder()

    env.use_case.execute(SIX_PM)

    assert env.devices.invalidated == ["token-a"]
    assert env.sleeps == []
    assert env.notifications()[0].push_sent_at is None


def _events(caplog, name):
    return [r.fields for r in caplog.records if r.getMessage() == name]


def test_each_notified_reminder_leaves_a_log_line_rf_not_02(env, caplog):
    caplog.set_level("INFO", logger="taia.reminders")
    reminder = env.reminder()

    env.use_case.execute(SIX_PM)

    [fields] = _events(caplog, "reminder_notified")
    assert fields == {
        "reminder_id": str(reminder.id), "user_id": str(USER), "push": "sent", "devices": 1, "attempts": 1,
    }


def test_log_says_why_no_push_was_sent_rf_not_04(env, caplog):
    caplog.set_level("INFO", logger="taia.reminders")
    env.devices.tokens[USER] = []
    env.reminder()

    env.use_case.execute(SIX_PM)

    assert [f["push"] for f in _events(caplog, "reminder_notified")] == ["no_devices"]
    assert "Recuerda" not in caplog.text
