"""Caso de uso: completar una tarea académica."""

from __future__ import annotations

import uuid

from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from backend.app.modules.academic.domain.entities.task import Task


class TaskNotFoundError(ValueError):
    """Se lanza cuando la tarea no existe o no pertenece al usuario."""


class CompleteTaskUseCase:
    """Marca como completada una tarea del usuario autenticado."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = self._repository.get_by_id(task_id, user_id)
        if task is None:
            raise TaskNotFoundError("La tarea no existe o no pertenece al usuario autenticado.")

        task.mark_done()
        return task
