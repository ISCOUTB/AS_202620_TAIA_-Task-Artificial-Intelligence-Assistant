"""Pruebas de integración del repositorio de tareas contra PostgreSQL (RF-TAR-04, RF-ASG-04, RT-03, RT-04).

Usan la fixture `clean_db` de conftest.py; sin TEST_DATABASE_URL se omiten.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.modules.academic.adapters.outbound.sqlalchemy_models import SubjectModel
from app.modules.academic.adapters.outbound.sqlalchemy_structure_repositories import SqlAlchemySubjectRepository
from app.modules.academic.adapters.outbound.sqlalchemy_task_repository import SqlAlchemyTaskRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery
from app.modules.academic.domain.entities.subject import Subject
from app.modules.academic.domain.entities.task import Task, TaskStatus, TaskType
from app.shared.clock import BOGOTA_TZ

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=BOGOTA_TZ)
USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


@pytest.fixture
def repos(clean_db):
    subjects = SqlAlchemySubjectRepository(clean_db)
    physics = Subject.create(USER, "Física")
    math = Subject.create(USER, "Matemáticas")
    foreign = Subject.create(OTHER_USER, "Física")
    for subject in (physics, math, foreign):
        subjects.add(subject)
    return SqlAlchemyTaskRepository(clean_db), physics, math, foreign, clean_db


def _task(subject: Subject, title: str, days: float, **kwargs) -> Task:
    return Task.create(subject.id, title, NOW + timedelta(days=days), now=NOW - timedelta(days=30), **kwargs)


def test_round_trip_keeps_bogota_times(repos):
    tasks, physics, *_ = repos
    task = _task(physics, "Informe", 2, type=TaskType.EXAM, description="Óptica")
    tasks.add(task)

    stored = tasks.get(task.id, USER)

    assert (stored.title, stored.type, stored.description) == ("Informe", TaskType.EXAM, "Óptica")
    assert stored.due_at == task.due_at
    assert stored.due_at.utcoffset() == timedelta(hours=-5)
    assert tasks.get(task.id, OTHER_USER) is None


def test_list_filters_in_database(repos):
    tasks, physics, math, foreign, _ = repos
    past = _task(physics, "Vencida", -1)
    done = _task(physics, "Hecha", 1)
    done.complete(NOW)
    for task in (past, done, _task(physics, "Pendiente física", 3), _task(math, "Parcial de derivadas", 5, type=TaskType.EXAM),
                 _task(foreign, "Ajena", 1)):
        tasks.add(task)

    def titles(**filters):
        items, total = tasks.list(USER, TaskQuery(**filters), NOW)
        return [task.title for task in items], total

    assert titles() == (["Vencida", "Hecha", "Pendiente física", "Parcial de derivadas"], 4)
    assert titles(status=TaskStatus.OVERDUE) == (["Vencida"], 1)
    assert titles(status=TaskStatus.COMPLETED) == (["Hecha"], 1)
    assert titles(status=TaskStatus.PENDING) == (["Pendiente física", "Parcial de derivadas"], 2)
    assert titles(subject_id=math.id) == (["Parcial de derivadas"], 1)
    assert titles(type=TaskType.EXAM) == (["Parcial de derivadas"], 1)
    assert titles(text="DERIVADAS") == (["Parcial de derivadas"], 1)
    assert titles(due_from=NOW + timedelta(days=2), due_to=NOW + timedelta(days=4)) == (["Pendiente física"], 1)
    assert titles(limit=2, offset=1) == (["Hecha", "Pendiente física"], 4)


def test_text_filter_escapes_like_wildcards(repos):
    tasks, physics, *_ = repos
    tasks.add(_task(physics, "Avance 100%", 1))
    tasks.add(_task(physics, "Avance 1000", 2))

    items, _ = tasks.list(USER, TaskQuery(text="100%"), NOW)

    assert [task.title for task in items] == ["Avance 100%"]


def test_deleted_tasks_are_hidden_but_counted_for_subject(repos):
    tasks, physics, *_ = repos
    task = _task(physics, "Borrada", 1)
    tasks.add(task)
    task.delete(NOW)
    tasks.save(task)

    assert tasks.get(task.id, USER) is None
    assert tasks.list(USER, TaskQuery(), NOW) == ([], 0)
    assert tasks.count_by_subject(physics.id) == 1
    assert tasks.count_open_by_subject(USER) == {}


def test_count_open_by_subject(repos):
    tasks, physics, math, *_ = repos
    done = _task(physics, "Hecha", 1)
    done.complete(NOW)
    for task in (done, _task(physics, "A", 1), _task(physics, "B", 2), _task(math, "C", 3)):
        tasks.add(task)

    assert tasks.count_open_by_subject(USER) == {physics.id: 2, math.id: 1}


def test_subject_with_tasks_cannot_be_deleted_in_database(repos):
    tasks, physics, _, _, session_factory = repos
    tasks.add(_task(physics, "Ancla", 1))

    with pytest.raises(IntegrityError):
        with session_factory.begin() as session:
            session.execute(delete(SubjectModel).where(SubjectModel.id == physics.id))
