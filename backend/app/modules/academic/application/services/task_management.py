"""Servicio de aplicación para operaciones de tareas académicas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.modules.academic.application.ports.inbound.task_management import (
    AcademicSubjectRef,
    AcademicTaskData,
    AcademicTaskManagement,
    AcademicTaskPage,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery, TaskRepository
from app.modules.academic.application.use_cases.manage_tasks import ManageTasksUseCase
from app.modules.academic.domain.entities.subject import normalize_text
from app.modules.academic.domain.entities.task import Task, TaskType
from app.shared.clock import Clock


class AcademicTaskManagementService(AcademicTaskManagement):
    """Fachada de aplicación que mantiene los repositorios dentro de Academic."""

    def __init__(self, tasks: TaskRepository, subjects: SubjectRepository, clock: Clock | None = None) -> None:
        self._use_case = ManageTasksUseCase(tasks, subjects, clock)
        self._subjects = subjects

    def create_task(
        self,
        user_id: UUID,
        subject_id: UUID,
        title: str,
        due_at: datetime,
        type: str = "task",
        description: str | None = None,
    ) -> AcademicTaskData:
        task = self._use_case.create(user_id, subject_id, title, due_at, TaskType(type), description)
        return self._to_data(task, user_id)

    def list_tasks(self, user_id: UUID, query: TaskQuery) -> AcademicTaskPage:
        tasks, total = self._use_case.list(user_id, query)
        names = self._subject_names(user_id)
        now = self._use_case.now()
        return AcademicTaskPage(
            items=[_to_data(task, user_id, names[task.subject_id], now) for task in tasks],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        return self._to_data(self._use_case.get(task_id, user_id), user_id)

    def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        title: str | None = None,
        description: str | None = None,
        subject_id: UUID | None = None,
        type: str | None = None,
        due_at: datetime | None = None,
    ) -> AcademicTaskData:
        task = self._use_case.update(
            task_id, user_id, title, description, subject_id, TaskType(type) if type else None, due_at
        )
        return self._to_data(task, user_id)

    def complete_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        return self._to_data(self._use_case.complete(task_id, user_id), user_id)

    def reopen_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        return self._to_data(self._use_case.reopen(task_id, user_id), user_id)

    def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        self._use_case.delete(task_id, user_id)

    def find_subject(self, user_id: UUID, text: str) -> AcademicSubjectRef | None:
        wanted = normalize_text(text or "")
        if not wanted:
            return None
        for subject in self._subjects.list_by_user(user_id):
            known = {subject.normalized_name, *(alias.normalized_alias for alias in subject.aliases)}
            if wanted in known:
                return AcademicSubjectRef(subject_id=subject.id, name=subject.name)
        return None

    def _subject_names(self, user_id: UUID) -> dict[UUID, str]:
        return {s.id: s.name for s in self._subjects.list_by_user(user_id, include_archived=True)}

    def _to_data(self, task: Task, user_id: UUID) -> AcademicTaskData:
        subject = self._subjects.get(task.subject_id, user_id)
        return _to_data(task, user_id, subject.name if subject else "", self._use_case.now())


def _to_data(task: Task, user_id: UUID, subject_name: str, now: datetime) -> AcademicTaskData:
    priority = task.priority(now)
    return AcademicTaskData(
        task_id=task.id,
        owner_user_id=user_id,
        subject_id=task.subject_id,
        subject_name=subject_name,
        type=task.type.value,
        title=task.title,
        description=task.description,
        due_at=task.due_at,
        completed_at=task.completed_at,
        status=task.status(now).value,
        priority=priority.value if priority else None,
        created_at=task.created_at,
    )
