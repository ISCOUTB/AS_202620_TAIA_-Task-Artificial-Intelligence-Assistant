"""Adaptador del contexto IA hacia el contexto académico.

Este adaptador traduce los DTO propios de IA a los puertos de entrada que
publica Academic (`AcademicTaskManagement` y `AcademicInsights`). No expone
entidades ni repositorios académicos al núcleo de IA. Los identificadores que
recibe los resolvió el backend (RF-AGT-10, RF-AGT-17), nunca el LLM.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.modules.academic.application.ports.inbound.academic_insights import (
    AcademicInsights,
    get_academic_insights,
)
from app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskData,
    AcademicTaskManagement,
    AcademicTaskQuery,
    get_academic_task_management,
)
from app.modules.ai.application.dto import (
    ClassView,
    NewTask,
    PeriodSummary,
    SubjectCounts,
    SubjectOption,
    TaskChanges,
    TaskFilters,
    TaskView,
)
from app.modules.ai.application.ports.academic_gateway import (
    AcademicError,
    AcademicGateway,
    TaskDataRejected,
)
from app.modules.ai.domain.messages import MAX_OPTIONS

# Tope de tareas que el agente consulta de una vez (máximo de RF-TAR-04).
_MAX_TASKS = 100


class AcademicGatewayAdapter(AcademicGateway):
    """Implementación real de AcademicGateway sobre los puertos de Academic."""

    def __init__(
        self,
        academic: AcademicTaskManagement | None = None,
        insights: AcademicInsights | None = None,
    ) -> None:
        self._academic = academic or get_academic_task_management()
        # AcademicInsights se busca al usarlo: el frente C lo configura en main.py
        # y el orden de composición no debe romper el arranque.
        self._insights = insights

    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        owner = _parse_user_id(user_id)
        subject_id = _parse_id(data.subject_id) if data.subject_id else self._subject_by_name(owner, data.subject)
        try:
            task = self._academic.create_task(
                user_id=owner,
                subject_id=subject_id,
                title=data.title,
                due_at=data.due_at,
                type=data.type,
                description=data.description,
            )
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        return _to_view(task)

    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        owner = _parse_user_id(user_id)
        query = AcademicTaskQuery(
            subject_id=_parse_id(filters.subject_id) if filters.subject_id else None,
            status=filters.status,
            due_from=filters.due_from,
            due_to=filters.due_to,
            text=filters.text,
            limit=_MAX_TASKS,
        )
        try:
            page = self._academic.list_tasks(owner, query)
        except ValueError as error:
            raise AcademicError(str(error)) from error
        tasks = [_to_view(task) for task in page.items]
        # AcademicTaskQuery todavía no filtra por tipo (P-D-01): se filtra la página.
        if filters.type:
            tasks = [task for task in tasks if task.type == filters.type]
        return tasks

    def update_task(self, user_id: str, task_id: str, changes: TaskChanges) -> TaskView:
        owner = _parse_user_id(user_id)
        try:
            task = self._academic.update_task(
                task_id=_parse_id(task_id),
                user_id=owner,
                title=changes.title,
                description=changes.description,
                subject_id=_parse_id(changes.subject_id) if changes.subject_id else None,
                due_at=changes.due_at,
            )
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        return _to_view(task)

    def complete_task(self, user_id: str, task_id: str) -> TaskView:
        owner = _parse_user_id(user_id)
        try:
            task = self._academic.complete_task(_parse_id(task_id), owner)
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        return _to_view(task)

    def match_subjects(self, user_id: str, text: str) -> list[SubjectOption]:
        owner = _parse_user_id(user_id)
        subjects = self._insights_port().match_subjects(owner, text, MAX_OPTIONS)
        return [SubjectOption(id=str(s.subject_id), name=s.name) for s in subjects]

    def summarize_period(self, user_id: str, start: datetime, end: datetime) -> PeriodSummary:
        owner = _parse_user_id(user_id)
        try:
            summary = self._insights_port().summarize_period(owner, start, end)
        except ValueError as error:
            raise AcademicError(str(error)) from error
        return PeriodSummary(
            start=summary.start,
            end=summary.end,
            pending=summary.pending,
            completed=summary.completed,
            overdue=summary.overdue,
            by_subject=[
                SubjectCounts(
                    name=item.subject_name,
                    pending=item.pending,
                    completed=item.completed,
                    overdue=item.overdue,
                )
                for item in summary.by_subject
            ],
            next_due=_to_view(summary.next_due) if summary.next_due else None,
        )

    def get_classes(self, user_id: str, start: datetime, end: datetime) -> list[ClassView]:
        owner = _parse_user_id(user_id)
        try:
            classes = self._insights_port().get_classes(owner, start, end)
        except ValueError as error:
            raise AcademicError(str(error)) from error
        return [
            ClassView(
                subject_id=str(item.subject_id),
                subject_name=item.subject_name,
                starts_at=item.starts_at,
                ends_at=item.ends_at,
                room=item.room,
            )
            for item in classes
        ]

    def _subject_by_name(self, owner: uuid.UUID, text: str | None) -> uuid.UUID:
        """Compatibilidad con quien crea por nombre exacto o alias (test_s8_closure)."""

        if not text:
            raise TaskDataRejected("Indica la asignatura de la tarea.")
        subject = self._academic.find_subject(owner, text)
        if subject is None:
            raise TaskDataRejected(
                f'No encontré la asignatura "{text}". Regístrala primero en la aplicación.'
            )
        return subject.subject_id

    def _insights_port(self) -> AcademicInsights:
        if self._insights is not None:
            return self._insights
        try:
            return get_academic_insights()
        except RuntimeError as error:
            raise AcademicError("El servicio académico no está disponible.") from error


def _parse_user_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as error:
        raise AcademicError("El identificador del usuario no es válido.") from error


def _parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as error:
        raise TaskDataRejected("El identificador no es válido.") from error


def _to_view(task: AcademicTaskData) -> TaskView:
    return TaskView(
        id=str(task.task_id),
        title=task.title,
        due_at=task.due_at,
        subject=task.subject_name,
        status=task.status,
        priority=task.priority,
        type=task.type,
        subject_id=str(task.subject_id),
    )
