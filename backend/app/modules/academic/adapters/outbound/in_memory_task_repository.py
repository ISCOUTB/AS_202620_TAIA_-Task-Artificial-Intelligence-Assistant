"""Repositorio de tareas en memoria para las pruebas.

Emula el JOIN con subjects para resolver el propietario y guarda copias, como
la base de datos.
"""

from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime

from app.modules.academic.adapters.outbound.in_memory_structure_repositories import (
    InMemorySubjectRepository,
)
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery, TaskRepository
from app.modules.academic.domain.entities.task import Task


class InMemoryTaskRepository(TaskRepository):
    def __init__(self, subjects: InMemorySubjectRepository) -> None:
        self._tasks: dict[uuid.UUID, Task] = {}
        self._subjects = subjects

    def add(self, task: Task) -> None:
        self._tasks[task.id] = deepcopy(task)

    def save(self, task: Task) -> None:
        self._tasks[task.id] = deepcopy(task)

    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        task = self._tasks.get(task_id)
        if task is None or task.deleted_at is not None or self._subjects.owner(task.subject_id) != user_id:
            return None
        return deepcopy(task)

    def list(self, user_id: uuid.UUID, query: TaskQuery, now: datetime) -> tuple[list[Task], int]:
        matching = sorted(
            (task for task in self._active(user_id) if _matches(task, query, now)),
            key=lambda task: task.due_at,
        )
        page = matching[query.offset : query.offset + query.limit]
        return [deepcopy(task) for task in page], len(matching)

    def count_by_subject(self, subject_id: uuid.UUID) -> int:
        return sum(1 for task in self._tasks.values() if task.subject_id == subject_id)

    def count_open_by_subject(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        counts: dict[uuid.UUID, int] = {}
        for task in self._active(user_id):
            if task.completed_at is None:
                counts[task.subject_id] = counts.get(task.subject_id, 0) + 1
        return counts

    def _active(self, user_id: uuid.UUID) -> list[Task]:
        return [
            task
            for task in self._tasks.values()
            if task.deleted_at is None and self._subjects.owner(task.subject_id) == user_id
        ]


def _matches(task: Task, query: TaskQuery, now: datetime) -> bool:
    if query.subject_id is not None and task.subject_id != query.subject_id:
        return False
    if query.status is not None and task.status(now) is not query.status:
        return False
    if query.type is not None and task.type is not query.type:
        return False
    if query.due_from is not None and task.due_at < query.due_from:
        return False
    if query.due_to is not None and task.due_at > query.due_to:
        return False
    if query.text:
        haystack = f"{task.title} {task.description or ''}".lower()
        if query.text.lower() not in haystack:
            return False
    return True
