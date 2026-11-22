"""Estadísticas del perfil ya agregadas (RF-PRF-01, RT-03, RT-04)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.academic.adapters.outbound.in_memory_structure_repositories import (
    InMemoryAcademicPeriodRepository,
    InMemorySubjectRepository,
)
from app.modules.academic.adapters.outbound.in_memory_task_repository import InMemoryTaskRepository
from app.modules.academic.application.errors import AcademicPeriodNotFoundError
from app.modules.academic.application.use_cases.profile_statistics import (
    ProfileStatisticsUseCase,
    StatisticsPeriod,
)
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.subject import Subject
from app.modules.academic.domain.entities.task import Task, TaskStatus
from app.shared.clock import BOGOTA_TZ, now_bogota
from tests.helpers import create_subject, future_iso, register_and_login

client = TestClient(app)

# Miércoles 10 de marzo de 2027 al mediodía, hora de Colombia.
NOW = datetime(2027, 3, 10, 12, 0, tzinfo=BOGOTA_TZ)


def _at(month: int, day: int, hour: int = 12) -> datetime:
    return datetime(2027, month, day, hour, 0, tzinfo=BOGOTA_TZ)


class World:
    def __init__(self) -> None:
        self.owner = uuid.uuid4()
        self.subjects = InMemorySubjectRepository()
        self.tasks = InMemoryTaskRepository(self.subjects)
        self.periods = InMemoryAcademicPeriodRepository()
        self.statistics = ProfileStatisticsUseCase(self.tasks, self.subjects, self.periods, clock=lambda: NOW)
        self.physics = self.subject("Física")
        self.math = self.subject("Matemáticas")
        self.chemistry = self.subject("Química")

    def subject(self, name: str) -> Subject:
        subject = Subject.create(self.owner, name)
        self.subjects.add(subject)
        return subject

    def task(self, subject: Subject, title: str, due_at: datetime, completed_at: datetime | None = None) -> Task:
        task = Task.create(subject.id, title, due_at, now=due_at - timedelta(days=30))
        task.completed_at = completed_at
        self.tasks.add(task)
        return task


@pytest.fixture
def world() -> World:
    world = World()
    world.task(world.physics, "A a tiempo", _at(3, 9, 10), completed_at=_at(3, 9, 9))
    world.task(world.physics, "B tarde", _at(3, 9, 12), completed_at=_at(3, 10, 8))
    world.task(world.physics, "C pendiente", _at(3, 11))
    world.task(world.math, "D vencida", _at(3, 9, 8))
    world.task(world.math, "E del mes", _at(3, 20))
    deleted = world.task(world.math, "F eliminada", _at(3, 12))
    deleted.delete(NOW)
    world.tasks.save(deleted)
    world.task(world.chemistry, "G archivada", _at(3, 12))
    world.chemistry.archive(NOW)
    world.subjects.save(world.chemistry)
    world.task(world.physics, "H antigua", _at(2, 20), completed_at=_at(2, 19))
    return world


def test_week_counts_by_status_without_deleted_and_with_archived_rf_prf_01(world):
    stats = world.statistics.statistics(world.owner, StatisticsPeriod.WEEK)

    assert (stats.start, stats.end) == (date(2027, 3, 8), date(2027, 3, 14))
    assert stats.by_status == {TaskStatus.PENDING: 2, TaskStatus.COMPLETED: 2, TaskStatus.OVERDUE: 1}


def test_on_time_means_completed_at_not_after_due_at_rf_prf_01(world):
    stats = world.statistics.statistics(world.owner, StatisticsPeriod.WEEK)

    assert (stats.on_time.completed, stats.on_time.on_time, stats.on_time.percentage) == (2, 1, 50.0)


def test_pending_load_by_subject_rf_prf_01(world):
    week = world.statistics.statistics(world.owner, StatisticsPeriod.WEEK)
    month = world.statistics.statistics(world.owner, StatisticsPeriod.MONTH)

    assert [(s.subject_name, s.pending) for s in week.pending_by_subject] == [
        ("Física", 1), ("Matemáticas", 1), ("Química", 1),
    ]
    assert (month.start, month.end) == (date(2027, 3, 1), date(2027, 3, 31))
    assert [(s.subject_name, s.pending) for s in month.pending_by_subject][0] == ("Matemáticas", 2)


def test_completed_by_week_covers_last_8_weeks_monday_to_sunday_rf_prf_01(world):
    weeks = world.statistics.statistics(world.owner, StatisticsPeriod.WEEK).completed_by_week

    assert [week.week_start for week in weeks] == [date(2027, 3, 8) - timedelta(weeks=n) for n in range(7, -1, -1)]
    assert {week.week_start: week.completed for week in weeks if week.completed} == {
        date(2027, 2, 15): 1,
        date(2027, 3, 8): 2,
    }


def test_upcoming_lists_pending_due_in_next_7_days_rf_prf_01(world):
    upcoming = world.statistics.statistics(world.owner, StatisticsPeriod.MONTH).upcoming

    assert [(task.title, task.subject_name) for task in upcoming] == [("C pendiente", "Física"), ("G archivada", "Química")]


def test_period_membership_is_by_due_at_and_weekly_chart_by_completed_at_rf_prf_01(world):
    world.task(world.math, "I adelantada", _at(4, 5), completed_at=_at(3, 9, 15))

    stats = world.statistics.statistics(world.owner, StatisticsPeriod.WEEK)

    assert stats.by_status == {TaskStatus.PENDING: 2, TaskStatus.COMPLETED: 2, TaskStatus.OVERDUE: 1}
    assert (stats.on_time.completed, stats.on_time.on_time) == (2, 1)
    assert {week.week_start: week.completed for week in stats.completed_by_week}[date(2027, 3, 8)] == 3


def test_on_time_percentage_is_rounded_to_one_decimal_rf_prf_01():
    world = World()
    world.task(world.physics, "A tiempo", _at(3, 9, 10), completed_at=_at(3, 9, 9))
    world.task(world.physics, "Tarde 1", _at(3, 9, 11), completed_at=_at(3, 9, 13))
    world.task(world.physics, "Tarde 2", _at(3, 9, 12), completed_at=_at(3, 9, 14))

    on_time = world.statistics.statistics(world.owner, StatisticsPeriod.WEEK).on_time

    assert (on_time.completed, on_time.on_time, on_time.percentage) == (3, 1, 33.3)


def test_academic_period_uses_its_dates_rf_prf_01(world):
    world.periods.save(AcademicPeriod(world.owner, date(2027, 2, 1), date(2027, 6, 30)))

    stats = world.statistics.statistics(world.owner, StatisticsPeriod.ACADEMIC_PERIOD)

    assert (stats.start, stats.end) == (date(2027, 2, 1), date(2027, 6, 30))
    assert stats.by_status[TaskStatus.COMPLETED] == 3


def test_academic_period_not_defined_raises(world):
    with pytest.raises(AcademicPeriodNotFoundError):
        world.statistics.statistics(world.owner, StatisticsPeriod.ACADEMIC_PERIOD)


def test_empty_period_has_null_percentage_rf_prf_01():
    statistics = ProfileStatisticsUseCase(
        InMemoryTaskRepository(InMemorySubjectRepository()), InMemorySubjectRepository(),
        InMemoryAcademicPeriodRepository(), clock=lambda: NOW,
    )

    stats = statistics.statistics(uuid.uuid4(), StatisticsPeriod.WEEK)

    assert stats.on_time.percentage is None
    assert (stats.pending_by_subject, stats.upcoming) == ([], [])
    assert len(stats.completed_by_week) == 8


def test_statistics_api_returns_aggregated_data_rf_prf_01():
    headers = register_and_login(client)
    today = now_bogota().date()
    client.put(
        "/academic/period",
        json={"start_date": (today - timedelta(days=30)).isoformat(), "end_date": (today + timedelta(days=60)).isoformat()},
        headers=headers,
    )
    subject_id = create_subject(client, headers, "Cálculo")
    ids = [
        client.post(
            "/academic/tasks", json={"subject_id": subject_id, "title": title, "due_at": future_iso(days=days)}, headers=headers
        ).json()["id"]
        for title, days in (("Taller", 2), ("Parcial", 3), ("Proyecto", 20))
    ]
    client.patch(f"/academic/tasks/{ids[0]}/complete", headers=headers)
    client.delete(f"/academic/tasks/{ids[1]}", headers=headers)

    response = client.get("/academic/statistics", params={"period": "academic_period"}, headers=headers)

    body = response.json()
    assert response.status_code == 200
    assert body["by_status"] == {"pending": 1, "completed": 1, "overdue": 0}
    assert body["on_time"] == {"completed": 1, "on_time": 1, "percentage": 100.0}
    assert body["pending_by_subject"] == [{"subject_id": subject_id, "subject_name": "Cálculo", "pending": 1}]
    assert body["upcoming"] == []
    assert len(body["completed_by_week"]) == 8
    assert body["completed_by_week"][-1]["completed"] == 1


def test_statistics_api_without_academic_period_returns_404():
    response = client.get("/academic/statistics", params={"period": "academic_period"}, headers=register_and_login(client))

    assert response.status_code == 404
    assert response.json() == {"detail": "No has definido un período académico."}


def test_statistics_api_rejects_unknown_period_and_requires_auth_rt_01():
    assert client.get("/academic/statistics", params={"period": "year"}, headers=register_and_login(client)).status_code == 422
    assert client.get("/academic/statistics", params={"period": "week"}).status_code == 401
