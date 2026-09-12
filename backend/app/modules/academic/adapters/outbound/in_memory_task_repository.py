"""Adaptador de persistencia en memoria para el módulo `academic`."""

from __future__ import annotations

import uuid

from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from backend.app.modules.academic.domain.entities.task import Task


class InMemoryTaskRepository(TaskRepository):
    """Repositorio en memoria con aislamiento de tareas por usuario."""

    def __init__(self) -> None:
        self._tasks: dict[uuid.UUID, Task] = {}

    def add(self, task: Task) -> None:
        self._tasks[task.id] = task

    def list_by_user(self, user_id: uuid.UUID) -> list[Task]:
        return [task for task in self._tasks.values() if task.user_id == user_id]

    def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        task = self._tasks.get(task_id)
        if task is None or task.user_id != user_id:
            return None
        return task
