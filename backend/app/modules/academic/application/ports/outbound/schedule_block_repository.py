"""Puerto de persistencia de bloques de horario."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday


class ScheduleBlockRepository(ABC):
    @abstractmethod
    def add(self, block: ScheduleBlock) -> None:
        """Persiste un bloque nuevo."""

    @abstractmethod
    def save(self, block: ScheduleBlock) -> None:
        """Persiste los cambios de un bloque existente."""

    @abstractmethod
    def get(self, block_id: uuid.UUID, user_id: uuid.UUID) -> ScheduleBlock | None:
        """Devuelve el bloque solo si su asignatura pertenece al usuario."""

    @abstractmethod
    def list_by_user(self, user_id: uuid.UUID, weekday: Weekday | None = None) -> list[ScheduleBlock]:
        """Bloques de las asignaturas activas del usuario, ordenados por día y hora de inicio."""

    @abstractmethod
    def list_by_subject(self, subject_id: uuid.UUID) -> list[ScheduleBlock]:
        """Bloques de una asignatura."""

    @abstractmethod
    def delete(self, block_id: uuid.UUID) -> None:
        """Elimina físicamente un bloque."""
