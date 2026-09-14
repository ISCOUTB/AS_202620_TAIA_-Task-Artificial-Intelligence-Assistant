"""Adaptador del contexto IA hacia el contexto académico.

Este adaptador traduce los DTO propios de IA a los casos de uso de Academic.
No expone entidades ni repositorios académicos al núcleo de IA.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from backend.app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskData,
    AcademicTaskManagement,
    get_academic_task_management,
)
from backend.app.modules.ai.application.dto import NewTask, TaskChanges, TaskFilters, TaskView
from backend.app.modules.ai.application.ports.academic_gateway import (
    AcademicGateway,
    AcademicError,
    TaskDataRejected,
)

_COLOMBIA_TZ = timezone(timedelta(hours=-5), "America/Bogota")


class AcademicGatewayAdapter(AcademicGateway):
    """Implementación real de AcademicGateway sobre los casos de uso de Academic."""

    def __init__(self, academic: AcademicTaskManagement | None = None) -> None:
        self._academic = academic or get_academic_task_management()

    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        try:
            task = self._academic.create_task(
                user_id=_parse_user_id(user_id),
                title=data.title,
                due_date=data.due_at.date(),
                subject=data.subject,
                description=data.description,
            )
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        except TypeError as error:
            raise TaskDataRejected("Los datos de la tarea no son válidos.") from error
        return _to_view(task)

    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        try:
            tasks = self._academic.list_tasks(_parse_user_id(user_id))
        except (ValueError, TypeError) as error:
            raise AcademicError("El identificador del usuario no es válido.") from error

        return [_to_view(task) for task in tasks if _matches(task, filters)]

    def update_task(self, user_id: str, task_id: str, changes: TaskChanges) -> TaskView:
        try:
            task = self._academic.update_task(
                task_id=uuid.UUID(task_id),
                user_id=_parse_user_id(user_id),
                title=changes.title,
                due_date=changes.due_at.date() if changes.due_at else None,
                subject=changes.subject,
                description=changes.description,
            )
        except ValueError as error:
            raise TaskDataRejected(str(error)) from error
        except TypeError as error:
            raise TaskDataRejected("Los datos de la tarea no son válidos.") from error
        return _to_view(task)


def _parse_user_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_view(task: AcademicTaskData) -> TaskView:
    # Academic actualmente almacena fecha, mientras que el contrato de IA usa
    # datetime. La adaptación conserva la fecha y usa medianoche local.
    due_at = datetime.combine(task.due_date, datetime.min.time(), tzinfo=_COLOMBIA_TZ)
    return TaskView(
        id=str(task.task_id),
        title=task.title,
        due_at=due_at,
        subject=task.subject,
        status=task.status,
    )


def _matches(task: AcademicTaskData, filters: TaskFilters) -> bool:
    if filters.text and filters.text.lower() not in task.title.lower():
        return False
    if filters.subject and filters.subject.lower() != (task.subject or "").lower():
        return False
    if filters.status and filters.status.lower() != task.status.lower():
        return False

    task_due = datetime.combine(task.due_date, datetime.min.time(), tzinfo=_COLOMBIA_TZ)
    if filters.due_from and task_due < filters.due_from:
        return False
    if filters.due_to and task_due > filters.due_to:
        return False
    return True
