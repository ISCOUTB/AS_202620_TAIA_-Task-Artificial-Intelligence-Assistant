"""`AcademicInsights`: resumen de un período, clases y resolución de asignaturas (RF-AGT-10, 12 y 13)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app as api
from app.modules.academic.adapters.outbound.in_memory_structure_repositories import (
    InMemoryAcademicPeriodRepository,
    InMemoryScheduleBlockRepository,
    InMemorySubjectRepository,
)
from app.modules.academic.adapters.outbound.in_memory_task_repository import InMemoryTaskRepository
from app.modules.academic.application.ports.inbound.academic_insights import get_academic_insights
from app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskQuery,
    get_academic_task_management,
)
from app.modules.academic.application.services.academic_insights import AcademicInsightsService
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject
from app.modules.academic.domain.entities.task import Task
from app.shared.clock import BOGOTA_TZ
from tests.helpers import create_subject, future_iso, register_and_login

client = TestClient(api)

NOW = datetime(2027, 3, 10, 12, 0, tzinfo=BOGOTA_TZ)
MARCH = (datetime(2027, 3, 1, tzinfo=BOGOTA_TZ), datetime(2027, 4, 1, tzinfo=BOGOTA_TZ))


class World:
    def __init__(self) -> None:
        self.owner = uuid.uuid4()
        self.subjects = InMemorySubjectRepository()
        self.tasks = InMemoryTaskRepository(self.subjects)
        self.blocks = InMemoryScheduleBlockRepository(self.subjects)
        self.periods = InMemoryAcademicPeriodRepository()
        calendar = AcademicCalendarUseCase(self.tasks, self.subjects, self.blocks, self.periods, clock=lambda: NOW)
        self.insights = AcademicInsightsService(self.tasks, self.subjects, calendar, clock=lambda: NOW)

    def subject(self, name: str, *aliases: str, owner: uuid.UUID | None = None) -> Subject:
        subject = Subject.create(owner or self.owner, name)
        for alias in aliases:
            subject.add_alias(alias)
        self.subjects.add(subject)
        return subject

    def task(self, subject: Subject, title: str, due_at: datetime, completed: bool = False, deleted: bool = False) -> Task:
        task = Task.create(subject.id, title, due_at, now=min(NOW, due_at) - timedelta(days=1))
        if completed:
            task.complete(due_at - timedelta(hours=1))
        if deleted:
            task.delete(NOW)
        self.tasks.add(task)
        return task


@pytest.fixture
def world() -> World:
    return World()


# RF-AGT-12 · resumen de un período


def test_summary_counts_by_status_and_subject_with_next_due_rf_agt_12(world):
    physics = world.subject("Física")
    math = world.subject("Matemáticas")
    world.task(physics, "Vencida", NOW - timedelta(days=2))
    world.task(physics, "Hecha", NOW - timedelta(days=1), completed=True)
    world.task(physics, "Próxima", NOW + timedelta(days=1))
    world.task(math, "Después", NOW + timedelta(days=5))
    world.task(math, "Abril", datetime(2027, 4, 2, tzinfo=BOGOTA_TZ))

    summary = world.insights.summarize_period(world.owner, *MARCH)

    assert (summary.pending, summary.completed, summary.overdue) == (2, 1, 1)
    assert [(s.subject_name, s.pending, s.completed, s.overdue) for s in summary.by_subject] == [
        ("Física", 1, 1, 1),
        ("Matemáticas", 1, 0, 0),
    ]
    assert summary.next_due.title == "Próxima"
    assert summary.next_due.subject_name == "Física"


def test_summary_period_membership_is_by_due_at_not_completed_at_rf_agt_12(world):
    physics = world.subject("Física")
    early = world.task(physics, "Adelantada de abril", datetime(2027, 4, 5, tzinfo=BOGOTA_TZ))
    early.complete(NOW)
    world.tasks.save(early)
    late = world.task(physics, "Vence en marzo", datetime(2027, 3, 3, tzinfo=BOGOTA_TZ))
    late.complete(datetime(2027, 4, 2, tzinfo=BOGOTA_TZ))
    world.tasks.save(late)

    summary = world.insights.summarize_period(world.owner, *MARCH)

    assert (summary.pending, summary.completed, summary.overdue) == (0, 1, 0)
    assert summary.next_due is None


def test_summary_ignores_deleted_tasks_and_other_users_rf_agt_12(world):
    physics = world.subject("Física")
    world.task(physics, "Borrada", NOW + timedelta(days=1), deleted=True)
    world.task(world.subject("Química", owner=uuid.uuid4()), "Ajena", NOW + timedelta(days=1))

    summary = world.insights.summarize_period(world.owner, *MARCH)

    assert (summary.pending, summary.completed, summary.overdue, summary.by_subject, summary.next_due) == (
        0, 0, 0, [], None
    )


def test_summary_counts_archived_subjects(world):
    physics = world.subject("Física")
    world.task(physics, "Hecha", NOW - timedelta(days=1), completed=True)
    physics.archive(NOW)
    world.subjects.save(physics)

    summary = world.insights.summarize_period(world.owner, *MARCH)

    assert [(s.subject_name, s.completed) for s in summary.by_subject] == [("Física", 1)]


# RF-AGT-13 · clases entre dos instantes


def test_get_classes_projects_schedule_in_order_rf_agt_13(world):
    physics = world.subject("Física")
    math = world.subject("Matemáticas")
    thursday = datetime(2027, 3, 11, tzinfo=BOGOTA_TZ)
    world.blocks.add(ScheduleBlock.create(physics.id, Weekday.THURSDAY, time(14), time(16), "Lab 3"))
    world.blocks.add(ScheduleBlock.create(math.id, Weekday.THURSDAY, time(7), time(9)))
    world.blocks.add(ScheduleBlock.create(math.id, Weekday.FRIDAY, time(7), time(9)))

    classes = world.insights.get_classes(world.owner, thursday, thursday + timedelta(days=1))

    assert [(c.subject_name, c.starts_at.hour, c.room) for c in classes] == [("Matemáticas", 7, None), ("Física", 14, "Lab 3")]
    assert all(c.starts_at.utcoffset() == timedelta(hours=-5) for c in classes)


def test_get_classes_only_inside_the_academic_period_rf_asg_08(world):
    """El agente usa el horario solo dentro del período académico (RF-ASG-08, RF-AGT-13)."""

    physics = world.subject("Física")
    world.blocks.add(ScheduleBlock.create(physics.id, Weekday.MONDAY, time(8), time(10)))
    world.periods.save(AcademicPeriod(world.owner, date(2027, 3, 8), date(2027, 3, 20)))

    classes = world.insights.get_classes(world.owner, *MARCH)

    assert [c.starts_at.date() for c in classes] == [date(2027, 3, 8), date(2027, 3, 15)]


# RF-AGT-10 · resolución de asignaturas


@pytest.mark.parametrize(
    "text",
    ["matematicas basicas", "MATEMÁTICAS BÁSICAS", "mate básicas", "mat bas", "MB", "matemáticas"],
)
def test_match_subjects_ignores_case_accents_and_accepts_prefixes_and_aliases_rf_agt_10(world, text):
    target = world.subject("Matemáticas Básicas", "MB")
    world.subject("Física")

    assert [ref.subject_id for ref in world.insights.match_subjects(world.owner, text)] == [target.id]


def test_exact_match_wins_over_prefixes_rf_agt_10(world):
    calculus = world.subject("Cálculo")
    world.subject("Cálculo Integral")

    assert [ref.subject_id for ref in world.insights.match_subjects(world.owner, "calculo")] == [calculus.id]


def test_ambiguous_text_returns_candidates_up_to_limit_rf_agt_10(world):
    for name in ("Historia Antigua", "Historia Moderna", "Historia de Colombia"):
        world.subject(name)

    matches = world.insights.match_subjects(world.owner, "historia", limit=2)

    assert [ref.name for ref in matches] == ["Historia Antigua", "Historia de Colombia"]


def test_match_subjects_skips_archived_and_other_users_rf_agt_10(world):
    archived = world.subject("Química")
    archived.archive(NOW)
    world.subjects.save(archived)
    world.subject("Química Orgánica", owner=uuid.uuid4())

    assert world.insights.match_subjects(world.owner, "quimica") == []


@pytest.mark.parametrize("text", ["", "   ", "biologia"])
def test_match_subjects_without_coincidence_is_empty_rf_agt_10(world, text):
    world.subject("Física")

    assert world.insights.match_subjects(world.owner, text) == []


def test_criterion_tasks_in_matematicas_basicas_rf_agt_10():
    """Criterio de RF-AGT-10 con los puertos que compone `main.py` sobre PostgreSQL."""

    headers = register_and_login(client)
    user_id = uuid.UUID(client.get("/users/me", headers=headers).json()["id"])
    math = create_subject(client, headers, "Matemáticas Básicas")
    physics = create_subject(client, headers, "Física")
    for subject_id, title in ((math, "Taller de límites"), (physics, "Informe de laboratorio")):
        client.post("/academic/tasks", json={"subject_id": subject_id, "title": title, "due_at": future_iso()}, headers=headers)

    [subject] = get_academic_insights().match_subjects(user_id, "matematicas basicas")
    page = get_academic_task_management().list_tasks(user_id, AcademicTaskQuery(subject_id=subject.subject_id))

    assert subject.name == "Matemáticas Básicas"
    assert [task.title for task in page.items] == ["Taller de límites"]
