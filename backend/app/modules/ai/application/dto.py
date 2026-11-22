"""Objetos que el modulo de IA intercambia con el modulo academico a traves
del puerto AcademicGateway. Son la forma del contrato, no entidades."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class NewTask:
    """Datos para crear una tarea. La validacion la hace academico.

    `subject_id` sale de `match_subjects`, nunca del modelo (RF-AGT-10, RF-AGT-17);
    `subject` es solo el nombre para mostrar."""

    title: str
    due_at: datetime
    subject: str | None = None
    description: str | None = None
    subject_id: str | None = None
    type: str = "task"


@dataclass(frozen=True)
class TaskChanges:
    """Campos a modificar de una tarea. None = no cambia."""

    title: str | None = None
    due_at: datetime | None = None
    subject: str | None = None
    description: str | None = None
    subject_id: str | None = None


@dataclass(frozen=True)
class TaskFilters:
    """Criterios para consultar tareas de un estudiante."""

    text: str | None = None
    subject_id: str | None = None
    status: str | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None
    type: str | None = None


@dataclass(frozen=True)
class TaskView:
    """Tarea tal como la devuelve academico para mostrarla."""

    id: str
    title: str
    due_at: datetime
    subject: str | None
    status: str
    priority: str | None = None
    type: str = "task"
    subject_id: str | None = None


@dataclass(frozen=True)
class SubjectOption:
    """Asignatura del estudiante que coincide con el texto del mensaje (RF-AGT-10)."""

    id: str
    name: str


@dataclass(frozen=True)
class SubjectCounts:
    name: str
    pending: int
    completed: int
    overdue: int


@dataclass(frozen=True)
class PeriodSummary:
    """Conteos de un periodo calculados por academico (RF-AGT-12)."""

    start: datetime
    end: datetime
    pending: int
    completed: int
    overdue: int
    by_subject: list[SubjectCounts] = field(default_factory=list)
    next_due: TaskView | None = None


@dataclass(frozen=True)
class ClassView:
    """Un bloque de clase en una fecha concreta (RF-AGT-13)."""

    subject_id: str
    subject_name: str
    starts_at: datetime
    ends_at: datetime
    room: str | None = None
