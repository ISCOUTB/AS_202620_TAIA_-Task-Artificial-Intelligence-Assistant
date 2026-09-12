"""Objetos que el modulo de IA intercambia con el modulo academico a traves
del puerto AcademicGateway. Son la forma del contrato, no entidades."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewTask:
    """Datos para crear una tarea. La validacion la hace academico."""

    title: str
    due_at: datetime
    subject: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class TaskChanges:
    """Campos a modificar de una tarea. None = no cambia."""

    title: str | None = None
    due_at: datetime | None = None
    subject: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class TaskFilters:
    """Criterios para consultar tareas de un estudiante."""

    text: str | None = None
    subject: str | None = None
    status: str | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None


@dataclass(frozen=True)
class TaskView:
    """Tarea tal como la devuelve academico para mostrarla."""

    id: str
    title: str
    due_at: datetime
    subject: str | None
    status: str
