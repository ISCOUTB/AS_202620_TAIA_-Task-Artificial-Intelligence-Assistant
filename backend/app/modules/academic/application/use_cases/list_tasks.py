"""Caso de uso: consultar las tareas académicas de un usuario (RF-02)."""

from __future__ import annotations

import uuid

from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from backend.app.modules.academic.domain.entities.task import Task


class ListTasksUseCase:
    """Devuelve únicamente las tareas pertenecientes al usuario solicitado."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(self, user_id: uuid.UUID) -> list[Task]:
        return self._repository.list_by_user(user_id)
