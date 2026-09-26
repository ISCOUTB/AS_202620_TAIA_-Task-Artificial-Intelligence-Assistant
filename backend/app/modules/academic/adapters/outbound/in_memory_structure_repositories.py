"""Repositorios en memoria de asignaturas, horario y período, para las pruebas.

Guardan y devuelven copias para comportarse como la base de datos: un cambio
en un objeto no se ve hasta que se llama a `save`.
"""

from __future__ import annotations

import uuid
from copy import deepcopy

from app.modules.academic.application.ports.outbound.academic_period_repository import (
    AcademicPeriodRepository,
)
from app.modules.academic.application.ports.outbound.schedule_block_repository import (
    ScheduleBlockRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject


class InMemorySubjectRepository(SubjectRepository):
    def __init__(self) -> None:
        self._subjects: dict[uuid.UUID, Subject] = {}

    def add(self, subject: Subject) -> None:
        self._subjects[subject.id] = deepcopy(subject)

    def save(self, subject: Subject) -> None:
        self._subjects[subject.id] = deepcopy(subject)

    def get(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject | None:
        subject = self._subjects.get(subject_id)
        if subject is None or subject.user_id != user_id:
            return None
        return deepcopy(subject)

    def get_by_normalized_name(self, user_id: uuid.UUID, normalized_name: str) -> Subject | None:
        for subject in self._subjects.values():
            if subject.user_id == user_id and subject.normalized_name == normalized_name:
                return deepcopy(subject)
        return None

    def list_by_user(self, user_id: uuid.UUID, include_archived: bool = False) -> list[Subject]:
        subjects = [
            deepcopy(subject)
            for subject in self._subjects.values()
            if subject.user_id == user_id and (include_archived or not subject.archived)
        ]
        return sorted(subjects, key=lambda subject: subject.normalized_name)

    def delete(self, subject_id: uuid.UUID) -> None:
        self._subjects.pop(subject_id, None)

    def owner_if_active(self, subject_id: uuid.UUID) -> uuid.UUID | None:
        subject = self._subjects.get(subject_id)
        return subject.user_id if subject is not None and not subject.archived else None

    def owner(self, subject_id: uuid.UUID) -> uuid.UUID | None:
        subject = self._subjects.get(subject_id)
        return subject.user_id if subject is not None else None


class InMemoryScheduleBlockRepository(ScheduleBlockRepository):
    """Emula el JOIN con subjects: los bloques de asignaturas borradas dejan de ser visibles."""

    def __init__(self, subjects: InMemorySubjectRepository) -> None:
        self._blocks: dict[uuid.UUID, ScheduleBlock] = {}
        self._subjects = subjects

    def add(self, block: ScheduleBlock) -> None:
        self._blocks[block.id] = deepcopy(block)

    def save(self, block: ScheduleBlock) -> None:
        self._blocks[block.id] = deepcopy(block)

    def get(self, block_id: uuid.UUID, user_id: uuid.UUID) -> ScheduleBlock | None:
        block = self._blocks.get(block_id)
        if block is None or self._subjects.owner(block.subject_id) != user_id:
            return None
        return deepcopy(block)

    def list_by_user(self, user_id: uuid.UUID, weekday: Weekday | None = None) -> list[ScheduleBlock]:
        blocks = [
            deepcopy(block)
            for block in self._blocks.values()
            if self._subjects.owner_if_active(block.subject_id) == user_id
            and (weekday is None or block.weekday == weekday)
        ]
        return sorted(blocks, key=lambda block: (block.weekday.order, block.start_time))

    def list_by_subject(self, subject_id: uuid.UUID) -> list[ScheduleBlock]:
        return [deepcopy(block) for block in self._blocks.values() if block.subject_id == subject_id]

    def delete(self, block_id: uuid.UUID) -> None:
        self._blocks.pop(block_id, None)


class InMemoryAcademicPeriodRepository(AcademicPeriodRepository):
    def __init__(self) -> None:
        self._periods: dict[uuid.UUID, AcademicPeriod] = {}

    def get(self, user_id: uuid.UUID) -> AcademicPeriod | None:
        period = self._periods.get(user_id)
        return deepcopy(period) if period is not None else None

    def save(self, period: AcademicPeriod) -> None:
        self._periods[period.user_id] = deepcopy(period)
