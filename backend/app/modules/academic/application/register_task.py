"""Caso de uso: registrar una tarea académica (RF-01, aspecto A-01)."""

from __future__ import annotations

from datetime import date

from backend.app.modules.academic.application.ports import TaskRepository
from backend.app.modules.academic.domain.task import Task


class RegisterTaskUseCase:
    """Coordina la creación y persistencia de una tarea académica."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(
        self,
        title: str,
        due_date: date,
        subject: str | None = None,
        description: str | None = None,
    ) -> Task:
        task = Task.create(
            title=title,
            due_date=due_date,
            subject=subject,
            description=description,
        )
        self._repository.add(task)
        return task
