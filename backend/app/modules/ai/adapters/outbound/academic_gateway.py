"""Adaptador del contexto IA hacia el contexto académico.

Este adaptador traduce los DTO propios de IA a los casos de uso de Academic.
No expone entidades ni repositorios académicos al núcleo de IA. La asignatura
llega como texto desde el LLM y aquí se resuelve a su identificador por
nombre o alias normalizado.
"""

from __future__ import annotations

import uuid

from app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskData,
    AcademicTaskManagement,
    AcademicTaskQuery,
    get_academic_task_management,
)
from app.modules.ai.application.dto import NewTask, TaskChanges, TaskFilters, TaskView
from app.modules.ai.application.ports.academic_gateway import (
    AcademicGateway,
    AcademicError,
    TaskDataRejected,
)

# Tope de tareas que el agente consulta de una vez.
_MAX_TASKS = 100

class AcademicGatewayAdapter(AcademicGateway):
    """Implementación real de AcademicGateway sobre los casos de uso de Academic."""

    def __init__(self, academic: AcademicTaskManagement | None = None) -> None:
        self._academic = academic or get_academic_task_management()

    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        owner = _parse_user_id(user_id)
        if not data.subject:
            raise TaskDataRejected("Indica la asignatura de la tarea.")
        subject_id = self._subject_id(owner, data.subject)
        try:
            task = self._academic.create_task(
                user_id=owner,
                subject_id=subject_id,
                title=data.title,
                due_at=data.due_at,
                description=data.description,
            )
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        return _to_view(task)

    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        owner = _parse_user_id(user_id)
        subject_id = None
        if filters.subject:
            subject = self._academic.find_subject(owner, filters.subject)
            if subject is None:
                return []
            subject_id = subject.subject_id
        query = AcademicTaskQuery(
            subject_id=subject_id,
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
        return [_to_view(task) for task in page.items]

    def update_task(self, user_id: str, task_id: str, changes: TaskChanges) -> TaskView:
        owner = _parse_user_id(user_id)
        subject_id = self._subject_id(owner, changes.subject) if changes.subject else None
        try:
            task = self._academic.update_task(
                task_id=uuid.UUID(task_id),
                user_id=owner,
                title=changes.title,
                description=changes.description,
                subject_id=subject_id,
                due_at=changes.due_at,
            )
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        return _to_view(task)

    def _subject_id(self, user_id: uuid.UUID, text: str) -> uuid.UUID:
        subject = self._academic.find_subject(user_id, text)
        if subject is None:
            raise TaskDataRejected(
                f'No encontré la asignatura "{text}". Regístrala primero en la aplicación.'
            )
        return subject.subject_id


def _parse_user_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as error:
        raise AcademicError("El identificador del usuario no es válido.") from error


def _to_view(task: AcademicTaskData) -> TaskView:
    return TaskView(
        id=str(task.task_id),
        title=task.title,
        due_at=task.due_at,
        subject=task.subject_name,
        status=task.status,
    )
