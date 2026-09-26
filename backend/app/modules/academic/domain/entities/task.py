"""Tareas y exámenes (RF-TAR-01…10)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from app.shared.clock import as_bogota, now_bogota


class TaskType(str, Enum):
    TASK = "task"
    EXAM = "exam"


class TaskStatus(str, Enum):
    """Estado derivado de `completed_at` y `due_at`; no se almacena (RF-TAR-09)."""

    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class TaskPriority(str, Enum):
    """Prioridad derivada del tiempo restante (RF-TAR-03, D-04)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


HIGH_PRIORITY_WINDOW = timedelta(hours=48)
MEDIUM_PRIORITY_WINDOW = timedelta(days=7)


class InvalidTaskError(ValueError):
    """Se lanza cuando los datos de una tarea violan una regla del dominio."""


@dataclass
class Task:
    """Actividad académica de una asignatura. El usuario propietario es el de la asignatura."""

    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    due_at: datetime
    type: TaskType = TaskType.TASK
    description: str | None = None
    completed_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=now_bogota)

    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 2000

    @staticmethod
    def create(
        subject_id: uuid.UUID,
        title: str,
        due_at: datetime,
        type: TaskType = TaskType.TASK,
        description: str | None = None,
        now: datetime | None = None,
    ) -> "Task":
        task = Task(
            id=uuid.uuid4(),
            subject_id=subject_id,
            title=_clean_title(title),
            due_at=_future_due_at(due_at, now),
            type=type,
            description=_clean_description(description),
        )
        return task

    def status(self, now: datetime | None = None) -> TaskStatus:
        if self.completed_at is not None:
            return TaskStatus.COMPLETED
        if self.due_at < (now or now_bogota()):
            return TaskStatus.OVERDUE
        return TaskStatus.PENDING

    def priority(self, now: datetime | None = None) -> TaskPriority | None:
        """Solo las tareas pendientes tienen prioridad."""

        current = now or now_bogota()
        if self.status(current) is not TaskStatus.PENDING:
            return None
        remaining = self.due_at - current
        if remaining <= HIGH_PRIORITY_WINDOW:
            return TaskPriority.HIGH
        if remaining <= MEDIUM_PRIORITY_WINDOW:
            return TaskPriority.MEDIUM
        return TaskPriority.LOW

    def update(
        self,
        title: str | None = None,
        description: str | None = None,
        subject_id: uuid.UUID | None = None,
        type: TaskType | None = None,
        due_at: datetime | None = None,
        now: datetime | None = None,
    ) -> None:
        if title is not None:
            self.title = _clean_title(title)
        if description is not None:
            self.description = _clean_description(description)
        if subject_id is not None:
            self.subject_id = subject_id
        if type is not None:
            self.type = type
        if due_at is not None:
            self.due_at = _future_due_at(due_at, now)

    def complete(self, now: datetime | None = None) -> None:
        """Idempotente: completar dos veces conserva el primer `completed_at` (RF-TAR-07)."""

        if self.completed_at is None:
            self.completed_at = now or now_bogota()

    def reopen(self) -> None:
        self.completed_at = None

    def delete(self, now: datetime | None = None) -> None:
        if self.deleted_at is None:
            self.deleted_at = now or now_bogota()


def _clean_title(title: str) -> str:
    clean = (title or "").strip()
    if not clean:
        raise InvalidTaskError("El título de la tarea no puede estar vacío.")
    if len(clean) > Task.MAX_TITLE_LENGTH:
        raise InvalidTaskError(f"El título de la tarea no puede superar {Task.MAX_TITLE_LENGTH} caracteres.")
    return clean


def _clean_description(description: str | None) -> str | None:
    clean = (description or "").strip()
    if len(clean) > Task.MAX_DESCRIPTION_LENGTH:
        raise InvalidTaskError(
            f"La descripción no puede superar {Task.MAX_DESCRIPTION_LENGTH} caracteres."
        )
    return clean or None


def _future_due_at(due_at: datetime, now: datetime | None) -> datetime:
    value = as_bogota(due_at)
    if value <= (now or now_bogota()):
        raise InvalidTaskError("La fecha límite debe ser posterior al momento actual.")
    return value
