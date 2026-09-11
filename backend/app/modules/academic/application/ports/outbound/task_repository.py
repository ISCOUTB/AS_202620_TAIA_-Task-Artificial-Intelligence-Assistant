"""Puerto de persistencia del contexto académico."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from backend.app.modules.academic.domain.entities.task import Task


class TaskRepository(ABC):
    """Contrato de persistencia para tareas pertenecientes a usuarios."""

    @abstractmethod
    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""

    @abstractmethod
    def list_by_user(self, user_id: uuid.UUID) -> list[Task]:
        """Devuelve únicamente las tareas pertenecientes al usuario indicado."""

    @abstractmethod
    def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        """Devuelve una tarea si pertenece al usuario indicado."""
