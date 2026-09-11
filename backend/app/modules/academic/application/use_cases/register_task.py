"""Caso de uso: registrar una tarea académica (RF-01)."""

from __future__ import annotations

import uuid
from datetime import date

from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from backend.app.modules.academic.domain.entities.task import Task


class RegisterTaskUseCase:
    """Coordina la creación y persistencia de una tarea académica."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(
        self,
        user_id: uuid.UUID,
        title: str,
        due_date: date,
        subject: str | None = None,
        description: str | None = None,
    ) -> Task:
        task = Task.create(
            user_id=user_id,
            title=title,
            due_date=due_date,
            subject=subject,
            description=description,
        )
        self._repository.add(task)
        return task
