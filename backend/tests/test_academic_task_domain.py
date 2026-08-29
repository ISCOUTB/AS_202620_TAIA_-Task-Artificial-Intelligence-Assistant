from datetime import date

import pytest

from backend.app.modules.academic.domain.task import InvalidTaskError, Task, TaskStatus


def test_create_task_with_valid_data():
    task = Task.create(title="Entregar informe", due_date=date(2026, 9, 1), subject="Cálculo")

    assert task.title == "Entregar informe"
    assert task.subject == "Cálculo"
    assert task.status == TaskStatus.PENDING
    assert task.id is not None


def test_create_task_strips_whitespace_from_title():
    task = Task.create(title="  Entregar informe  ", due_date=date(2026, 9, 1))

    assert task.title == "Entregar informe"


def test_create_task_rejects_empty_title():
    with pytest.raises(InvalidTaskError):
        Task.create(title="   ", due_date=date(2026, 9, 1))


def test_create_task_rejects_title_too_long():
    with pytest.raises(InvalidTaskError):
        Task.create(title="a" * 201, due_date=date(2026, 9, 1))


def test_mark_done_changes_status():
    task = Task.create(title="Entregar informe", due_date=date(2026, 9, 1))

    task.mark_done()

    assert task.status == TaskStatus.DONE
