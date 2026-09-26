"""Composición del repositorio académico en memoria para la ejecución local."""

from app.modules.academic.adapters.outbound.in_memory_task_repository import (
    InMemoryTaskRepository,
)
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository


_repository: TaskRepository = InMemoryTaskRepository()


def get_task_repository() -> TaskRepository:
    """Devuelve la instancia compartida del repositorio académico."""

    return _repository
