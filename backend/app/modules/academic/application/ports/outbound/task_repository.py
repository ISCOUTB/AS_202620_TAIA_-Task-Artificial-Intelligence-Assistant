"""Puerto de persistencia de tareas."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.modules.academic.domain.entities.task import Task, TaskStatus, TaskType


@dataclass(frozen=True)
class TaskQuery:
    """Filtros de RF-TAR-04. `None` significa "sin filtrar por ese campo"."""

    subject_id: uuid.UUID | None = None
    status: TaskStatus | None = None
    type: TaskType | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None
    text: str | None = None
    limit: int = 20
    offset: int = 0


class TaskRepository(ABC):
    """Las tareas eliminadas lógicamente nunca se devuelven (RT-04)."""

    @abstractmethod
    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""

    @abstractmethod
    def save(self, task: Task) -> None:
        """Persiste los cambios de una tarea, incluido su borrado lógico."""

    @abstractmethod
    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        """Devuelve la tarea si su asignatura pertenece al usuario y no está eliminada."""

    @abstractmethod
    def list(self, user_id: uuid.UUID, query: TaskQuery, now: datetime) -> tuple[list[Task], int]:
        """Página de tareas ordenadas por fecha límite y el total que cumple los filtros.

        `now` define qué tareas están vencidas al filtrar por estado.
        """

    @abstractmethod
    def count_by_subject(self, subject_id: uuid.UUID) -> int:
        """Todas las tareas de la asignatura, incluidas las eliminadas (RF-ASG-04)."""

    @abstractmethod
    def count_open_by_subject(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        """Tareas no completadas ni eliminadas por asignatura del usuario (RF-ASG-02)."""
