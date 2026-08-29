"""Adaptador de persistencia en memoria para el módulo `academic`.

Implementa el puerto `TaskRepository` sin depender de PostgreSQL. Es un
adaptador temporal: existe para tener un corte vertical ejecutable de
punta a punta (API → aplicación → dominio → persistencia) en esta entrega.
Cuando se incorpore el adaptador real de PostgreSQL, bastará con
implementar `TaskRepository` sobre esa tecnología y cambiar la instancia
inyectada en `adapters/api.py`; el dominio y los casos de uso no se
modifican (ver ADR-0001).
"""

from __future__ import annotations

import uuid

from backend.app.modules.academic.application.ports import TaskRepository
from backend.app.modules.academic.domain.task import Task


class InMemoryTaskRepository(TaskRepository):
    """Repositorio en memoria de tareas académicas (no persistente entre reinicios)."""

    def __init__(self) -> None:
        self._tasks: dict[uuid.UUID, Task] = {}

    def add(self, task: Task) -> None:
        self._tasks[task.id] = task

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())

    def get(self, task_id: uuid.UUID) -> Task | None:
        return self._tasks.get(task_id)
