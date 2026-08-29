"""Puertos (interfaces) que la capa de aplicación necesita de su infraestructura.

Siguiendo ADR-0001, el módulo `academic` define aquí el contrato que
cualquier adaptador de persistencia debe cumplir. Los casos de uso dependen
únicamente de esta interfaz, nunca de un motor de base de datos concreto.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from backend.app.modules.academic.domain.task import Task


class TaskRepository(ABC):
    """Puerto de persistencia para tareas académicas."""

    @abstractmethod
    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""

    @abstractmethod
    def list_all(self) -> list[Task]:
        """Devuelve todas las tareas registradas."""

    @abstractmethod
    def get(self, task_id: uuid.UUID) -> Task | None:
        """Devuelve una tarea por su identificador, o None si no existe."""
