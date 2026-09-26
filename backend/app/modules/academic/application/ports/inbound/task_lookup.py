"""Puerto de entrada para consultas académicas consumidas por otros contextos."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class AcademicTaskSummary:
    task_id: UUID
    owner_user_id: UUID
    title: str
    due_date: date | None


class AcademicTaskLookup(Protocol):
    """Contrato público del contexto Academic para consultar una tarea."""

    def get_summary(self, task_id: UUID, user_id: UUID) -> AcademicTaskSummary | None:
        ...


_service: AcademicTaskLookup | None = None


def configure_academic_task_lookup(service: AcademicTaskLookup) -> None:
    global _service
    _service = service


def get_academic_task_lookup() -> AcademicTaskLookup:
    if _service is None:
        raise RuntimeError("El servicio de consulta académica no ha sido configurado.")
    return _service
