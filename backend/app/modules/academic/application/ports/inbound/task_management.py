"""Puerto de entrada para operaciones académicas consumidas por otros contextos."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.academic.application.ports.outbound.task_repository import TaskQuery


@dataclass(frozen=True)
class AcademicTaskData:
    """Datos académicos publicados sin exponer la entidad de dominio."""

    task_id: UUID
    owner_user_id: UUID
    subject_id: UUID
    subject_name: str
    type: str
    title: str
    description: str | None
    due_at: datetime
    completed_at: datetime | None
    status: str
    priority: str | None
    created_at: datetime


@dataclass(frozen=True)
class AcademicTaskPage:
    items: list[AcademicTaskData]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class AcademicSubjectRef:
    subject_id: UUID
    name: str


class AcademicTaskManagement(Protocol):
    """Contrato público para gestionar tareas y resolver asignaturas."""

    def create_task(
        self,
        user_id: UUID,
        subject_id: UUID,
        title: str,
        due_at: datetime,
        type: str = "task",
        description: str | None = None,
    ) -> AcademicTaskData:
        ...

    def list_tasks(self, user_id: UUID, query: TaskQuery) -> AcademicTaskPage:
        ...

    def get_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        ...

    def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        title: str | None = None,
        description: str | None = None,
        subject_id: UUID | None = None,
        type: str | None = None,
        due_at: datetime | None = None,
    ) -> AcademicTaskData:
        ...

    def complete_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        ...

    def reopen_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        ...

    def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        ...

    def find_subject(self, user_id: UUID, text: str) -> AcademicSubjectRef | None:
        """Asignatura activa cuyo nombre o alias normalizado coincide con el texto."""
        ...


_service: AcademicTaskManagement | None = None


def configure_academic_task_management(service: AcademicTaskManagement) -> None:
    global _service
    _service = service


def get_academic_task_management() -> AcademicTaskManagement:
    if _service is None:
        raise RuntimeError("El servicio de gestión académica no ha sido configurado.")
    return _service
