"""Puerto de entrada para operaciones académicas consumidas por otros contextos."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class AcademicTaskData:
    """Datos académicos publicados sin exponer la entidad de dominio."""

    task_id: UUID
    owner_user_id: UUID
    title: str
    due_date: date
    subject: str | None
    description: str | None
    status: str


class AcademicTaskManagement(Protocol):
    """Contrato público para crear, consultar y actualizar tareas académicas."""

    def create_task(
        self,
        user_id: UUID,
        title: str,
        due_date: date,
        subject: str | None = None,
        description: str | None = None,
    ) -> AcademicTaskData:
        ...

    def list_tasks(self, user_id: UUID) -> list[AcademicTaskData]:
        ...

    def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        title: str | None = None,
        due_date: date | None = None,
        subject: str | None = None,
        description: str | None = None,
    ) -> AcademicTaskData:
        ...

    def complete_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        ...


_service: AcademicTaskManagement | None = None


def configure_academic_task_management(service: AcademicTaskManagement) -> None:
    global _service
    _service = service


def get_academic_task_management() -> AcademicTaskManagement:
    if _service is None:
        raise RuntimeError("El servicio de gestión académica no ha sido configurado.")
    return _service
