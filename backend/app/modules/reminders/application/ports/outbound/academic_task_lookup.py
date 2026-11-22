"""Puerto de salida de Reminders para leer los datos de una actividad de Academic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TaskInfo:
    """Lo que Reminders necesita de una actividad (RF-REC-01, RF-NOT-02)."""

    task_id: UUID
    title: str
    subject_name: str
    due_at: datetime
    completed: bool


class AcademicTaskLookup(ABC):
    @abstractmethod
    def get(self, task_id: UUID, user_id: UUID) -> TaskInfo | None:
        """`None` si la actividad no existe, está eliminada o es de otro usuario."""
        raise NotImplementedError
