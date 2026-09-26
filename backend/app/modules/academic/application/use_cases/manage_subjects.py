"""Casos de uso de asignaturas (RF-ASG-01…05, RF-ASG-09)."""

from __future__ import annotations

import uuid

from app.modules.academic.application.errors import (
    AliasNotFoundError,
    ScheduleOverlapError,
    SubjectAlreadyExistsError,
    SubjectHasTasksError,
    SubjectNotFoundError,
)
from app.modules.academic.application.ports.outbound.schedule_block_repository import (
    ScheduleBlockRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from app.modules.academic.domain.entities.subject import Subject


class ManageSubjectsUseCase:
    def __init__(self, subjects: SubjectRepository, blocks: ScheduleBlockRepository, tasks: TaskRepository) -> None:
        self._subjects = subjects
        self._blocks = blocks
        self._tasks = tasks

    def create(self, user_id: uuid.UUID, name: str, teacher: str | None = None) -> Subject:
        subject = Subject.create(user_id=user_id, name=name, teacher=teacher)
        self._ensure_unique_name(subject)
        self._subjects.add(subject)
        return subject

    def list(self, user_id: uuid.UUID, include_archived: bool = False) -> list[Subject]:
        return self._subjects.list_by_user(user_id, include_archived=include_archived)

    def get(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject:
        subject = self._subjects.get(subject_id, user_id)
        if subject is None:
            raise SubjectNotFoundError("La asignatura no existe o no pertenece al usuario.")
        return subject

    def update(
        self,
        subject_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str | None = None,
        teacher: str | None = None,
    ) -> Subject:
        subject = self.get(subject_id, user_id)
        if name is not None:
            subject.rename(name)
            self._ensure_unique_name(subject)
        if teacher is not None:
            subject.set_teacher(teacher)
        self._subjects.save(subject)
        return subject

    def delete(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> None:
        subject = self.get(subject_id, user_id)
        # Cuenta también las tareas eliminadas lógicamente, que siguen referenciando la asignatura.
        task_count = self._tasks.count_by_subject(subject.id)
        if task_count > 0:
            raise SubjectHasTasksError(
                f"La asignatura tiene {task_count} actividad(es) asociada(s); archívala en lugar de eliminarla."
            )
        self._subjects.delete(subject.id)

    def pending_task_counts(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        return self._tasks.count_open_by_subject(user_id)

    def archive(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject:
        subject = self.get(subject_id, user_id)
        subject.archive()
        self._subjects.save(subject)
        return subject

    def unarchive(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject:
        subject = self.get(subject_id, user_id)
        if not subject.archived:
            return subject
        # Sus bloques vuelven al horario: no pueden chocar con los bloques activos.
        active_blocks = self._blocks.list_by_user(user_id)
        for block in self._blocks.list_by_subject(subject.id):
            if any(block.overlaps(active) for active in active_blocks):
                raise ScheduleOverlapError(
                    "No se puede desarchivar: su horario se solapa con otra asignatura activa."
                )
        subject.unarchive()
        self._subjects.save(subject)
        return subject

    def add_alias(self, subject_id: uuid.UUID, user_id: uuid.UUID, alias: str) -> Subject:
        subject = self.get(subject_id, user_id)
        subject.add_alias(alias)
        self._subjects.save(subject)
        return subject

    def remove_alias(self, subject_id: uuid.UUID, user_id: uuid.UUID, alias_id: uuid.UUID) -> Subject:
        subject = self.get(subject_id, user_id)
        if not subject.remove_alias(alias_id):
            raise AliasNotFoundError("El alias no existe en esta asignatura.")
        self._subjects.save(subject)
        return subject

    def _ensure_unique_name(self, subject: Subject) -> None:
        existing = self._subjects.get_by_normalized_name(subject.user_id, subject.normalized_name)
        if existing is not None and existing.id != subject.id:
            raise SubjectAlreadyExistsError("Ya tienes una asignatura con ese nombre.")
