"""Servicio de aplicación para consultas de tareas académicas."""

from uuid import UUID

from backend.app.modules.academic.application.ports.inbound.task_lookup import (
    AcademicTaskLookup,
    AcademicTaskSummary,
)
from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository


class AcademicTaskLookupService(AcademicTaskLookup):
    """Expone solo la consulta necesaria a contextos consumidores."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def get_summary(self, task_id: UUID, user_id: UUID) -> AcademicTaskSummary | None:
        task = self._repository.get_by_id(task_id, user_id)
        if task is None:
            return None
        return AcademicTaskSummary(
            task_id=task.id,
            owner_user_id=task.user_id,
            title=task.title,
            due_date=getattr(task, "due_date", None),
        )
