"""RF-REC-02 · Política de recordatorios por defecto (función pura)."""

from datetime import datetime, timedelta, timezone

from app.modules.reminders.domain.policy import default_schedule
from app.shared.clock import BOGOTA_TZ


def bogota(day: int, hour: int, minute: int = 0, month: int = 10) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=BOGOTA_TZ)


def test_acceptance_criterion_rf_rec_02():
    """Creada el 1-oct 10:00, vence el 8-oct 23:59: el 2, 4, 6 y 7 de octubre a las 18:00."""

    schedule = default_schedule(due_at=bogota(8, 23, 59), now=bogota(1, 10))

    assert schedule == [bogota(2, 18), bogota(4, 18), bogota(6, 18), bogota(7, 18)]


def test_hours_are_colombian_even_if_inputs_come_in_utc_rf_rec_02_rt_03():
    due_utc = bogota(8, 23, 59).astimezone(timezone.utc)
    now_utc = bogota(1, 10).astimezone(timezone.utc)

    schedule = default_schedule(due_at=due_utc, now=now_utc)

    assert [moment.astimezone(BOGOTA_TZ).hour for moment in schedule] == [18, 18, 18, 18]
    assert schedule[0] == datetime(2026, 10, 2, 23, 0, tzinfo=timezone.utc)


def test_only_within_the_14_days_before_due_rf_rec_02():
    due = bogota(30, 12)

    schedule = default_schedule(due_at=due, now=bogota(1, 10))

    assert schedule[0] == bogota(16, 18)
    assert len(schedule) == 8
    assert all(moment < due for moment in schedule)


def test_only_future_moments_rf_rec_02():
    schedule = default_schedule(due_at=bogota(8, 23, 59), now=bogota(6, 18))

    assert schedule == [bogota(7, 18)]


def test_single_reminder_60_minutes_before_when_none_is_future_rf_rec_02():
    due = bogota(8, 12)

    schedule = default_schedule(due_at=due, now=bogota(7, 19))

    assert schedule == [due - timedelta(minutes=60)]


def test_nothing_when_60_minutes_or_less_remain_rf_rec_02():
    due = bogota(8, 12)

    assert default_schedule(due_at=due, now=due - timedelta(minutes=60)) == []
    assert default_schedule(due_at=due, now=due + timedelta(days=1)) == []
