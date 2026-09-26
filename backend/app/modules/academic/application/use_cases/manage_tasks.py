"""Casos de uso de tareas y exámenes (RF-TAR-01, 03…10)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.modules.academic.application.errors import (
    SubjectArchivedError,
    SubjectNotFoundError,
    TaskNotFoundError,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery, TaskRepository
from app.modules.academic.domain.entities.task import Task, TaskType
from app.shared.clock import Clock, now_bogota

MAX_PAGE_SIZE = 100


class ManageTasksUseCase:
    def __init__(self, tasks: TaskRepository, subjects: SubjectRepository, clock: Clock | None = None) -> None:
        self._tasks = tasks
        self._subjects = subjects
        self._now = clock or now_bogota

    def create(
        self,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
        title: str,
        due_at: datetime,
        type: TaskType = TaskType.TASK,
        description: str | None = None,
    ) -> Task:
        self._ensure_active_subject(subject_id, user_id)
        task = Task.create(subject_id, title, due_at, type, description, now=self._now())
        self._tasks.add(task)
        return task

    def list(self, user_id: uuid.UUID, query: TaskQuery) -> tuple[list[Task], int]:
        if not 1 <= query.limit <= MAX_PAGE_SIZE:
            raise ValueError(f"El tamaño de página debe estar entre 1 y {MAX_PAGE_SIZE}.")
        if query.offset < 0:
            raise ValueError("El desplazamiento no puede ser negativo.")
        return self._tasks.list(user_id, query, self._now())

    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = self._tasks.get(task_id, user_id)
        if task is None:
            raise TaskNotFoundError("La tarea no existe o no pertenece al usuario autenticado.")
        return task

    def update(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        subject_id: uuid.UUID | None = None,
        type: TaskType | None = None,
        due_at: datetime | None = None,
    ) -> Task:
        task = self.get(task_id, user_id)
        if subject_id is not None and subject_id != task.subject_id:
            self._ensure_active_subject(subject_id, user_id)
        task.update(title, description, subject_id, type, due_at, now=self._now())
        self._tasks.save(task)
        return task

    def complete(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = self.get(task_id, user_id)
        task.complete(self._now())
        self._tasks.save(task)
        return task

    def reopen(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = self.get(task_id, user_id)
        task.reopen()
        self._tasks.save(task)
        return task

    def delete(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        task = self.get(task_id, user_id)
        task.delete(self._now())
        self._tasks.save(task)

    def now(self) -> datetime:
        return self._now()

    def _ensure_active_subject(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> None:
        subject = self._subjects.get(subject_id, user_id)
        if subject is None:
            raise SubjectNotFoundError("La asignatura no existe o no pertenece al usuario.")
        if subject.archived:
            raise SubjectArchivedError("La asignatura está archivada y no acepta tareas nuevas.")
