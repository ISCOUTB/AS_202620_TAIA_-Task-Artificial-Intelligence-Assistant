"""Caso de uso: consultar las tareas académicas registradas (RF-02)."""

from __future__ import annotations

from backend.app.modules.academic.application.ports import TaskRepository
from backend.app.modules.academic.domain.task import Task


class ListTasksUseCase:
    """Devuelve las tareas registradas, delegando la lectura al repositorio."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Task]:
        return self._repository.list_all()
