"""Entidades y reglas del dominio académico."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class TaskStatus(str, Enum):
    """Estado de una tarea académica."""

    PENDING = "pending"
    DONE = "done"


class InvalidTaskError(ValueError):
    """Se lanza cuando los datos de una tarea violan una regla del dominio."""


@dataclass
class Task:
    """Tarea académica perteneciente a un estudiante."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    due_date: date
    subject: str | None = None
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    MAX_TITLE_LENGTH = 200

    @staticmethod
    def create(
        user_id: uuid.UUID,
        title: str,
        due_date: date,
        subject: str | None = None,
        description: str | None = None,
    ) -> "Task":
        """Crea una tarea nueva aplicando las reglas de validación del dominio."""

        if not isinstance(user_id, uuid.UUID):
            raise InvalidTaskError("El identificador del usuario no es válido.")

        clean_title = (title or "").strip()
        if not clean_title:
            raise InvalidTaskError("El título de la tarea no puede estar vacío.")
        if len(clean_title) > Task.MAX_TITLE_LENGTH:
            raise InvalidTaskError(
                f"El título de la tarea no puede superar {Task.MAX_TITLE_LENGTH} caracteres."
            )

        return Task(
            id=uuid.uuid4(),
            user_id=user_id,
            title=clean_title,
            due_date=due_date,
            subject=subject.strip() if subject else None,
            description=description.strip() if description else None,
        )

    def mark_done(self) -> None:
        """Marca la tarea como completada."""

        self.status = TaskStatus.DONE
