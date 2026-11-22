"""Calendario académico: actividades, exámenes y clases proyectadas en un rango (RF-TAR-11, RF-ASG-08, RT-03)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.academic.adapters.outbound.in_memory_structure_repositories import (
    InMemoryAcademicPeriodRepository,
    InMemoryScheduleBlockRepository,
    InMemorySubjectRepository,
)
from app.modules.academic.adapters.outbound.in_memory_task_repository import InMemoryTaskRepository
from app.modules.academic.application.errors import InvalidCalendarRangeError
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject
from app.modules.academic.domain.entities.task import Task, TaskType
from app.shared.clock import BOGOTA_TZ, now_bogota
from tests.helpers import create_subject, register_and_login

client = TestClient(app)

# Lunes 1 de marzo de 2027; el reloj está una semana antes.
MONDAY = date(2027, 3, 1)
NOW = datetime(2027, 2, 22, 9, 0, tzinfo=BOGOTA_TZ)


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=BOGOTA_TZ)


class World:
    def __init__(self) -> None:
        self.owner = uuid.uuid4()
        self.subjects = InMemorySubjectRepository()
        self.tasks = InMemoryTaskRepository(self.subjects)
        self.blocks = InMemoryScheduleBlockRepository(self.subjects)
        self.periods = InMemoryAcademicPeriodRepository()
        self.calendar = AcademicCalendarUseCase(self.tasks, self.subjects, self.blocks, self.periods, clock=lambda: NOW)

    def subject(self, name: str, owner: uuid.UUID | None = None) -> Subject:
        subject = Subject.create(owner or self.owner, name)
        self.subjects.add(subject)
        return subject

    def task(self, subject: Subject, title: str, due_at: datetime, type: TaskType = TaskType.TASK) -> Task:
        task = Task.create(subject.id, title, due_at, type, now=NOW)
        self.tasks.add(task)
        return task

    def block(self, subject: Subject, weekday: Weekday, start: time, end: time, room: str | None = None) -> None:
        self.blocks.add(ScheduleBlock.create(subject.id, weekday, start, end, room))


@pytest.fixture
def world() -> World:
    return World()


def test_calendar_lists_tasks_exams_and_projected_classes_rf_tar_11(world):
    physics = world.subject("Física")
    world.task(physics, "Informe", _at(MONDAY + timedelta(days=2), 23, 59))
    world.task(physics, "Parcial", _at(MONDAY + timedelta(days=4), 8), TaskType.EXAM)
    world.block(physics, Weekday.MONDAY, time(8), time(10), "A-101")
    world.block(physics, Weekday.THURSDAY, time(14), time(16))

    result = world.calendar.calendar(world.owner, MONDAY, MONDAY + timedelta(days=13))

    assert [(task.title, task.type) for task in result.tasks] == [("Informe", "task"), ("Parcial", "exam")]
    assert [(c.starts_at, c.ends_at, c.room) for c in result.classes] == [
        (_at(MONDAY, 8), _at(MONDAY, 10), "A-101"),
        (_at(MONDAY + timedelta(days=3), 14), _at(MONDAY + timedelta(days=3), 16), None),
        (_at(MONDAY + timedelta(days=7), 8), _at(MONDAY + timedelta(days=7), 10), "A-101"),
        (_at(MONDAY + timedelta(days=10), 14), _at(MONDAY + timedelta(days=10), 16), None),
    ]
    assert {c.subject_name for c in result.classes} == {"Física"}


def test_calendar_includes_both_ends_of_the_range_in_bogota_time_rt_03(world):
    physics = world.subject("Física")
    world.task(physics, "Primer día", _at(MONDAY, 0))
    world.task(physics, "Último día", _at(MONDAY + timedelta(days=1), 23, 59))
    world.task(physics, "Fuera", _at(MONDAY + timedelta(days=2), 0))

    result = world.calendar.calendar(world.owner, MONDAY, MONDAY + timedelta(days=1))

    assert [task.title for task in result.tasks] == ["Primer día", "Último día"]


def test_task_at_21h_bogota_belongs_to_that_day_not_the_next_rt_03(world):
    physics = world.subject("Física")
    world.task(physics, "Noche", _at(MONDAY, 21))

    assert [t.title for t in world.calendar.calendar(world.owner, MONDAY, MONDAY).tasks] == ["Noche"]
    assert world.calendar.calendar(world.owner, MONDAY + timedelta(days=1), MONDAY + timedelta(days=1)).tasks == []


def test_classes_are_only_projected_inside_the_academic_period_rf_asg_08(world):
    physics = world.subject("Física")
    world.block(physics, Weekday.MONDAY, time(8), time(10))
    world.periods.save(AcademicPeriod(world.owner, MONDAY + timedelta(days=7), MONDAY + timedelta(days=60)))

    result = world.calendar.calendar(world.owner, MONDAY, MONDAY + timedelta(days=13))

    assert [c.starts_at.date() for c in result.classes] == [MONDAY + timedelta(days=7)]


def test_archived_subject_classes_are_hidden_but_tasks_remain_rf_asg_05(world):
    physics = world.subject("Física")
    world.task(physics, "Informe", _at(MONDAY, 12))
    world.block(physics, Weekday.MONDAY, time(8), time(10))
    physics.archive(NOW)
    world.subjects.save(physics)

    result = world.calendar.calendar(world.owner, MONDAY, MONDAY)

    assert result.classes == []
    assert [(t.title, t.subject_name) for t in result.tasks] == [("Informe", "Física")]


def test_calendar_excludes_deleted_tasks_and_other_users_data_rt_02_rt_04(world):
    physics = world.subject("Física")
    deleted = world.task(physics, "Borrada", _at(MONDAY, 12))
    deleted.delete(NOW)
    world.tasks.save(deleted)
    other = world.subject("Química", owner=uuid.uuid4())
    world.task(other, "Ajena", _at(MONDAY, 12))
    world.block(other, Weekday.MONDAY, time(8), time(10))

    result = world.calendar.calendar(world.owner, MONDAY, MONDAY)

    assert (result.tasks, result.classes) == ([], [])


def test_calendar_rejects_end_before_start_rf_tar_11(world):
    with pytest.raises(InvalidCalendarRangeError):
        world.calendar.calendar(world.owner, MONDAY, MONDAY - timedelta(days=1))


def test_calendar_accepts_31_days_including_both_ends_rf_tar_11(world):
    result = world.calendar.calendar(world.owner, MONDAY, MONDAY + timedelta(days=30))

    assert (result.start, result.end) == (MONDAY, MONDAY + timedelta(days=30))


def test_calendar_rejects_more_than_31_days_rf_tar_11(world):
    with pytest.raises(InvalidCalendarRangeError):
        world.calendar.calendar(world.owner, MONDAY, MONDAY + timedelta(days=31))


def test_calendar_api_returns_tasks_and_classes_rf_tar_11():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers, "Cálculo")
    tomorrow = now_bogota().date() + timedelta(days=1)
    weekday = list(Weekday)[tomorrow.weekday()].value
    block = client.post(
        "/academic/schedule-blocks",
        json={"subject_id": subject_id, "weekday": weekday, "start_time": "07:00", "end_time": "09:00", "room": "B2"},
        headers=headers,
    )
    assert block.status_code == 201, block.text
    exam = client.post(
        "/academic/tasks",
        json={"subject_id": subject_id, "title": "Parcial", "type": "exam", "due_at": f"{tomorrow.isoformat()}T10:00:00"},
        headers=headers,
    )
    assert exam.status_code == 201, exam.text

    response = client.get(
        "/academic/calendar", params={"start": tomorrow.isoformat(), "end": tomorrow.isoformat()}, headers=headers
    )

    body = response.json()
    assert response.status_code == 200
    assert (body["start"], body["end"]) == (tomorrow.isoformat(), tomorrow.isoformat())
    assert [(t["title"], t["type"], t["subject_name"]) for t in body["tasks"]] == [("Parcial", "exam", "Cálculo")]
    assert body["classes"] == [{
        "subject_id": subject_id,
        "subject_name": "Cálculo",
        "starts_at": f"{tomorrow.isoformat()}T07:00:00-05:00",
        "ends_at": f"{tomorrow.isoformat()}T09:00:00-05:00",
        "room": "B2",
    }]


def test_calendar_api_projects_classes_only_inside_the_academic_period_rf_asg_08():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers, "Cálculo")
    client.post(
        "/academic/schedule-blocks",
        json={"subject_id": subject_id, "weekday": "monday", "start_time": "07:00", "end_time": "09:00"},
        headers=headers,
    )
    saved = client.put("/academic/period", json={"start_date": "2027-03-08", "end_date": "2027-03-20"}, headers=headers)
    assert saved.status_code == 200, saved.text

    body = client.get("/academic/calendar", params={"start": "2027-03-01", "end": "2027-03-31"}, headers=headers).json()

    assert [c["starts_at"] for c in body["classes"]] == ["2027-03-08T07:00:00-05:00", "2027-03-15T07:00:00-05:00"]


def test_calendar_api_hides_other_users_events_rt_02():
    owner = register_and_login(client)
    subject_id = create_subject(client, owner)
    day = now_bogota().date() + timedelta(days=2)
    client.post("/academic/tasks", json={"subject_id": subject_id, "title": "Privada", "due_at": day.isoformat()}, headers=owner)

    body = client.get(
        "/academic/calendar", params={"start": day.isoformat(), "end": day.isoformat()}, headers=register_and_login(client)
    ).json()

    assert body["tasks"] == []


def test_calendar_api_rejects_incoherent_range_with_422_rf_tar_11():
    headers = register_and_login(client)

    response = client.get("/academic/calendar", params={"start": "2027-03-10", "end": "2027-03-01"}, headers=headers)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_calendar_api_rejects_range_longer_than_31_days_with_422_rf_tar_11():
    headers = register_and_login(client)

    response = client.get("/academic/calendar", params={"start": "2027-03-01", "end": "2027-04-01"}, headers=headers)

    assert response.status_code == 422
    assert "31" in response.json()["detail"]


def test_calendar_api_accepts_a_31_day_range_rf_tar_11():
    headers = register_and_login(client)

    response = client.get("/academic/calendar", params={"start": "2027-03-01", "end": "2027-03-31"}, headers=headers)

    assert response.status_code == 200


def test_calendar_api_requires_authentication_rt_01():
    assert client.get("/academic/calendar", params={"start": "2027-03-01", "end": "2027-03-02"}).status_code == 401
