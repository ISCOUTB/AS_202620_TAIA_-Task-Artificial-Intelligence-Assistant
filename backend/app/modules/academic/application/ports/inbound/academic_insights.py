"""Puerto de entrada de Academic para resúmenes y horario.

El agente lo usa para RF-AGT-12 (resumen de un período) y RF-AGT-13 (consultar
el horario). Los conteos y la proyección del horario los calcula el backend; el
LLM no hace cálculos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.academic.application.ports.inbound.task_management import (
    AcademicSubjectRef,
    AcademicTaskData,
)


@dataclass(frozen=True)
class SubjectTaskCounts:
    subject_id: UUID
    subject_name: str
    pending: int
    completed: int
    overdue: int


@dataclass(frozen=True)
class AcademicPeriodSummary:
    """Conteos del período `[start, end)`, agrupados por asignatura (RF-AGT-12)."""

    start: datetime
    end: datetime
    pending: int
    completed: int
    overdue: int
    by_subject: list[SubjectTaskCounts]
    next_due: AcademicTaskData | None


@dataclass(frozen=True)
class ClassOccurrence:
    """Un bloque de clase proyectado en una fecha concreta (hora de Colombia)."""

    subject_id: UUID
    subject_name: str
    starts_at: datetime
    ends_at: datetime
    room: str | None


class AcademicInsights(Protocol):
    """Contrato público de Academic para resúmenes y horario."""

    def summarize_period(
        self, user_id: UUID, start: datetime, end: datetime
    ) -> AcademicPeriodSummary:
        ...

    def get_classes(self, user_id: UUID, start: datetime, end: datetime) -> list[ClassOccurrence]:
        """Clases entre `start` y `end`, ordenadas por inicio."""
        ...

    def match_subjects(self, user_id: UUID, text: str, limit: int = 5) -> list[AcademicSubjectRef]:
        """Asignaturas activas que coinciden con `text` (RF-AGT-10).

        Sin distinguir mayúsculas ni tildes, con prefijos, abreviaturas y alias.
        Una sola coincidencia clara devuelve una lista de un elemento.
        """
        ...


_service: AcademicInsights | None = None


def configure_academic_insights(service: AcademicInsights) -> None:
    global _service
    _service = service


def get_academic_insights() -> AcademicInsights:
    if _service is None:
        raise RuntimeError("El servicio de resúmenes académicos no ha sido configurado.")
    return _service
