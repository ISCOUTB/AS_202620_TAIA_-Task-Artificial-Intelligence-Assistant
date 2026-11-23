"""Servicio de aplicación para operaciones de tareas académicas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.modules.academic.application.ports.inbound.task_management import (
    AcademicSubjectRef,
    AcademicTaskData,
    AcademicTaskManagement,
    AcademicTaskPage,
    AcademicTaskQuery,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery, TaskRepository
from app.modules.academic.application.use_cases.manage_tasks import ManageTasksUseCase
from app.modules.academic.domain.entities.subject import normalize_text
from app.modules.academic.domain.entities.task import Task, TaskType, TaskStatus
from app.modules.reminders.application.ports.inbound.task_reminder_sync import (
    ReminderPlan,
    TaskReminderReader,
    TaskReminderSync,
    TaskReminderView,
    get_task_reminder_reader,
)
from app.shared.clock import Clock


class AcademicTaskManagementService(AcademicTaskManagement):
    """Fachada de aplicación que mantiene los repositorios dentro de Academic."""

    def __init__(
        self,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        clock: Clock | None = None,
        reminders: TaskReminderSync | None = None,
        reminder_reader: TaskReminderReader | None = None,
    ) -> None:
        self._use_case = ManageTasksUseCase(tasks, subjects, clock, reminders)
        self._subjects = subjects
        self._reminder_reader = reminder_reader

    def create_task(
        self,
        user_id: UUID,
        subject_id: UUID,
        title: str,
        due_at: datetime,
        type: str = "task",
        description: str | None = None,
        *,
        reminders: ReminderPlan | None = None,
    ) -> AcademicTaskData:
        """`reminders` solo lo usa la API; el agente no lo envía y recibe la política por defecto (RF-AGT-07)."""

        task = self._use_case.create(user_id, subject_id, title, due_at, TaskType(type), description, reminders)
        return self._to_data(task, user_id)

    def list_tasks(self, user_id: UUID, query: AcademicTaskQuery | TaskQuery) -> AcademicTaskPage:
        """Filtros de RF-TAR-04 aplicados en la consulta. Un `type` desconocido lanza `ValueError`."""

        if isinstance(query, AcademicTaskQuery):
            aliases = {"done": TaskStatus.COMPLETED, "completed": TaskStatus.COMPLETED,
                       "pending": TaskStatus.PENDING, "overdue": TaskStatus.OVERDUE}
            query = TaskQuery(
                subject_id=query.subject_id,
                statuses=tuple(
                    status for status in [aliases.get((query.status or "").lower())] if status is not None
                ),
                type=TaskType(query.type.lower()) if query.type else None,
                due_from=query.due_from, due_to=query.due_to,
                text=query.text, limit=query.limit, offset=query.offset,
            )
        tasks, total = self._use_case.list(user_id, query)
        names = self._subject_names(user_id)
        now = self._use_case.now()
        return AcademicTaskPage(
            items=[to_task_data(task, user_id, names[task.subject_id], now) for task in tasks],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        return self._to_data(self._use_case.get(task_id, user_id), user_id)

    def get_task_detail(self, task_id: UUID, user_id: UUID) -> tuple[AcademicTaskData, list[TaskReminderView]]:
        """Actividad propia con sus recordatorios, leídos por el puerto de Reminders (RF-TAR-05)."""

        task = self.get_task(task_id, user_id)
        reader = self._reminder_reader or get_task_reminder_reader()
        return task, reader.list_for_task(user_id, task_id)

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
        return to_task_data(task, user_id, subject.name if subject else "", self._use_case.now())


def to_task_data(task: Task, user_id: UUID, subject_name: str, now: datetime) -> AcademicTaskData:
    """Publica la tarea con su estado y su prioridad calculados en `now` (RF-TAR-03, RF-TAR-09)."""

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
