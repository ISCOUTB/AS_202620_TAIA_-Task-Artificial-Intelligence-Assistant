"""Puerto de persistencia de asignaturas."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.modules.academic.domain.entities.subject import Subject


class SubjectRepository(ABC):
    @abstractmethod
    def add(self, subject: Subject) -> None:
        """Persiste una asignatura nueva con sus alias."""

    @abstractmethod
    def save(self, subject: Subject) -> None:
        """Persiste los cambios de una asignatura existente, incluidos sus alias."""

    @abstractmethod
    def get(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject | None:
        """Devuelve la asignatura solo si pertenece al usuario."""

    @abstractmethod
    def get_by_normalized_name(self, user_id: uuid.UUID, normalized_name: str) -> Subject | None:
        """Busca una asignatura del usuario por su nombre normalizado."""

    @abstractmethod
    def list_by_user(self, user_id: uuid.UUID, include_archived: bool = False) -> list[Subject]:
        """Asignaturas del usuario ordenadas por nombre."""

    @abstractmethod
    def delete(self, subject_id: uuid.UUID) -> None:
        """Elimina físicamente la asignatura, sus alias y sus bloques de horario."""
