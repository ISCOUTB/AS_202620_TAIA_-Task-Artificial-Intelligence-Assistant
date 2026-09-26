"""Reglas del dominio de tareas (RF-TAR-01, 03, 07…10, RT-03)."""

from datetime import datetime, timedelta
import uuid

import pytest

from app.modules.academic.domain.entities.task import InvalidTaskError, Task, TaskPriority, TaskStatus, TaskType
from app.shared.clock import BOGOTA_TZ

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=BOGOTA_TZ)


def _task(due_in: timedelta = timedelta(days=3), **kwargs) -> Task:
    return Task.create(uuid.uuid4(), kwargs.pop("title", "Entregar informe"), NOW + due_in, now=NOW, **kwargs)


def test_create_task_with_valid_data():
    task = _task(type=TaskType.EXAM, description="  Capítulos 1 a 3  ")

    assert task.title == "Entregar informe"
    assert task.type is TaskType.EXAM
    assert task.description == "Capítulos 1 a 3"
    assert task.status(NOW) is TaskStatus.PENDING


def test_create_task_strips_whitespace_from_title():
    assert _task(title="  Entregar informe  ").title == "Entregar informe"


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_create_task_rejects_invalid_title(title):
    with pytest.raises(InvalidTaskError):
        _task(title=title)


def test_create_task_rejects_description_too_long():
    with pytest.raises(InvalidTaskError):
        _task(description="x" * 2001)


def test_due_at_must_be_in_the_future():
    with pytest.raises(InvalidTaskError):
        _task(due_in=timedelta(minutes=-1))


def test_naive_due_at_is_interpreted_as_bogota_time():
    task = Task.create(uuid.uuid4(), "Tarea", datetime(2026, 10, 5, 21, 0), now=NOW)

    assert task.due_at == datetime(2026, 10, 5, 21, 0, tzinfo=BOGOTA_TZ)


@pytest.mark.parametrize(
    ("due_in", "expected"),
    [
        (timedelta(hours=30), TaskPriority.HIGH),
        (timedelta(hours=48), TaskPriority.HIGH),
        (timedelta(days=5), TaskPriority.MEDIUM),
        (timedelta(days=7), TaskPriority.MEDIUM),
        (timedelta(days=8), TaskPriority.LOW),
    ],
)
def test_priority_depends_on_remaining_time_rf_tar_03(due_in, expected):
    assert _task(due_in=due_in).priority(NOW) is expected


def test_priority_changes_with_time_without_editing():
    task = _task(due_in=timedelta(days=5))

    assert task.priority(NOW) is TaskPriority.MEDIUM
    assert task.priority(NOW + timedelta(days=4)) is TaskPriority.HIGH


def test_overdue_is_derived_rf_tar_09():
    task = _task(due_in=timedelta(hours=1))

    assert task.status(NOW + timedelta(hours=2)) is TaskStatus.OVERDUE
    assert task.priority(NOW + timedelta(hours=2)) is None


def test_complete_is_idempotent_and_keeps_first_completed_at_rf_tar_07():
    task = _task()
    task.complete(NOW)
    task.complete(NOW + timedelta(hours=1))

    assert task.completed_at == NOW
    assert task.status(NOW) is TaskStatus.COMPLETED
    assert task.priority(NOW) is None


def test_reopen_clears_completed_at_rf_tar_08():
    task = _task()
    task.complete(NOW)
    task.reopen()

    assert task.completed_at is None
    assert task.status(NOW) is TaskStatus.PENDING


def test_update_validates_new_due_at():
    task = _task()

    with pytest.raises(InvalidTaskError):
        task.update(due_at=NOW - timedelta(days=1), now=NOW)
