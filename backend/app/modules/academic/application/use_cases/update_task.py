"""Caso de uso: actualizar una tarea académica."""

from __future__ import annotations

import uuid
from datetime import date

from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from backend.app.modules.academic.domain.entities.task import InvalidTaskError, Task


class TaskNotFoundError(ValueError):
    """Se lanza cuando la tarea no existe o no pertenece al usuario."""


class UpdateTaskUseCase:
    """Actualiza únicamente una tarea perteneciente al usuario autenticado."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        due_date: date | None = None,
        subject: str | None = None,
        description: str | None = None,
    ) -> Task:
        task = self._repository.get_by_id(task_id, user_id)
        if task is None:
            raise TaskNotFoundError(
                "La tarea no existe o no pertenece al usuario autenticado."
            )

        try:
            task.update(
                title=title,
                due_date=due_date,
                subject=subject,
                description=description,
            )
        except InvalidTaskError:
            raise
        return task
