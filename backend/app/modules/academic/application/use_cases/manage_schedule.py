"""Casos de uso del horario de clases (RF-ASG-06, RF-ASG-07)."""

from __future__ import annotations

import uuid
from datetime import time

from app.modules.academic.application.errors import (
    ScheduleBlockNotFoundError,
    ScheduleOverlapError,
    SubjectArchivedError,
    SubjectNotFoundError,
)
from app.modules.academic.application.ports.outbound.schedule_block_repository import (
    ScheduleBlockRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject


class ManageScheduleUseCase:
    def __init__(self, subjects: SubjectRepository, blocks: ScheduleBlockRepository) -> None:
        self._subjects = subjects
        self._blocks = blocks

    def create(
        self,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
        weekday: Weekday,
        start_time: time,
        end_time: time,
        room: str | None = None,
    ) -> ScheduleBlock:
        self._active_subject(subject_id, user_id)
        block = ScheduleBlock.create(subject_id, weekday, start_time, end_time, room)
        self._ensure_no_overlap(block, user_id)
        self._blocks.add(block)
        return block

    def list(self, user_id: uuid.UUID, weekday: Weekday | None = None) -> list[ScheduleBlock]:
        return self._blocks.list_by_user(user_id, weekday=weekday)

    def update(
        self,
        block_id: uuid.UUID,
        user_id: uuid.UUID,
        subject_id: uuid.UUID | None = None,
        weekday: Weekday | None = None,
        start_time: time | None = None,
        end_time: time | None = None,
        room: str | None = None,
    ) -> ScheduleBlock:
        block = self._get(block_id, user_id)
        if subject_id is not None:
            self._active_subject(subject_id, user_id)
            block.subject_id = subject_id
        block.update(weekday=weekday, start_time=start_time, end_time=end_time, room=room)
        self._ensure_no_overlap(block, user_id)
        self._blocks.save(block)
        return block

    def delete(self, block_id: uuid.UUID, user_id: uuid.UUID) -> None:
        block = self._get(block_id, user_id)
        self._blocks.delete(block.id)

    def _get(self, block_id: uuid.UUID, user_id: uuid.UUID) -> ScheduleBlock:
        block = self._blocks.get(block_id, user_id)
        if block is None:
            raise ScheduleBlockNotFoundError("El bloque de horario no existe o no pertenece al usuario.")
        return block

    def _active_subject(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject:
        subject = self._subjects.get(subject_id, user_id)
        if subject is None:
            raise SubjectNotFoundError("La asignatura no existe o no pertenece al usuario.")
        if subject.archived:
            raise SubjectArchivedError("La asignatura está archivada.")
        return subject

    def _ensure_no_overlap(self, block: ScheduleBlock, user_id: uuid.UUID) -> None:
        for other in self._blocks.list_by_user(user_id, weekday=block.weekday):
            if block.overlaps(other):
                raise ScheduleOverlapError(
                    f"El bloque se solapa con otra clase de {other.start_time:%H:%M} a {other.end_time:%H:%M}."
                )
