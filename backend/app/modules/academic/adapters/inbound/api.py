"""Adaptador HTTP de tareas y exámenes (RF-TAR-01…10)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, BeforeValidator, Field

from app.modules.academic.application.errors import (
    SubjectNotFoundError,
    TaskNotFoundError,
)
from app.modules.academic.application.ports.inbound.task_management import AcademicTaskData
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery
from app.modules.academic.application.services.task_management import AcademicTaskManagementService
from app.modules.academic.domain.entities.task import TaskStatus, TaskType
from app.modules.reminders.application.ports.inbound.task_reminder_sync import (
    ReminderMode,
    ReminderPlan,
    TaskReminderView,
)
from app.shared.adapters.inbound.auth import CurrentUserId
from app.shared.clock import end_of_day_bogota

router = APIRouter(prefix="/academic/tasks", tags=["academic"])

_service: AcademicTaskManagementService | None = None


def configure_task_api(service: AcademicTaskManagementService) -> None:
    """La compone `main.py` con la misma instancia que publica `AcademicTaskManagement`."""

    global _service
    _service = service


def get_task_management() -> AcademicTaskManagementService:
    if _service is None:
        raise RuntimeError("La API de tareas académicas no está configurada.")
    return _service


TaskManagement = Annotated[AcademicTaskManagementService, Depends(get_task_management)]


def _parse_due_at(value: Any) -> Any:
    """Solo una fecha AAAA-MM-DD se interpreta como las 23:59 de Colombia (RT-03)."""

    if isinstance(value, str) and len(value.strip()) == 10:
        return end_of_day_bogota(date.fromisoformat(value.strip()))
    return value


DueAt = Annotated[
    datetime,
    BeforeValidator(_parse_due_at),
    Field(description="Fecha y hora límite. Solo con fecha (AAAA-MM-DD) se asume 23:59 hora de Colombia; sin zona horaria, hora de Colombia."),
]


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por el adaptador cuando la petición falla."""

    detail: str


NOT_FOUND = {404: {"model": ErrorResponse, "description": "La tarea o la asignatura no existe o no pertenece al usuario."}}
INVALID = {422: {"model": ErrorResponse, "description": "Los datos de la tarea no son válidos."}}


def _http_error(error: ValueError) -> HTTPException:
    if isinstance(error, (TaskNotFoundError, SubjectNotFoundError)):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


class ReminderOptionRequest(BaseModel):
    """Opción de recordatorios al crear una actividad (RF-TAR-02)."""

    mode: ReminderMode = Field(
        default="default",
        description="`none`: sin recordatorios; `default`: política por defecto (RF-REC-02); `custom`: las fechas de `custom_at`.",
    )
    custom_at: list[datetime] = Field(
        default_factory=list,
        description="Solo con `custom`: entre una y 10 fechas futuras y anteriores a la fecha límite. Sin zona horaria, hora de Colombia.",
    )

    def to_plan(self) -> ReminderPlan:
        return ReminderPlan(mode=self.mode, custom_at=tuple(self.custom_at))


class TaskCreateRequest(BaseModel):
    """Esquema de entrada para registrar una tarea o un examen."""

    subject_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=200)
    due_at: DueAt
    type: TaskType = TaskType.TASK
    description: str | None = Field(default=None, max_length=2000)
    reminders: ReminderOptionRequest | None = Field(
        default=None, description="Sin este campo se aplica la política por defecto (RF-TAR-02)."
    )


class TaskUpdateRequest(BaseModel):
    """Campos opcionales para actualizar una tarea."""

    subject_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_at: DueAt | None = None
    type: TaskType | None = None
    description: str | None = Field(default=None, max_length=2000)


class TaskResponse(BaseModel):
    """Tarea con sus campos derivados: estado y prioridad (RF-TAR-03, RF-TAR-09)."""

    id: uuid.UUID
    subject_id: uuid.UUID
    subject_name: str
    type: TaskType
    title: str
    description: str | None
    due_at: datetime
    completed_at: datetime | None
    status: TaskStatus
    priority: str | None
    created_at: datetime

    @classmethod
    def from_data(cls, task: AcademicTaskData) -> "TaskResponse":
        return cls(
            id=task.task_id,
            subject_id=task.subject_id,
            subject_name=task.subject_name,
            type=task.type,
            title=task.title,
            description=task.description,
            due_at=task.due_at,
            completed_at=task.completed_at,
            status=task.status,
            priority=task.priority,
            created_at=task.created_at,
        )


class TaskReminderResponse(BaseModel):
    """Recordatorio de la actividad, tal como lo publica Reminders (RF-TAR-05, RF-REC-03)."""

    id: uuid.UUID
    scheduled_at: datetime
    message: str
    origin: str
    status: str

    @classmethod
    def from_view(cls, reminder: TaskReminderView) -> "TaskReminderResponse":
        return cls(
            id=reminder.reminder_id,
            scheduled_at=reminder.scheduled_at,
            message=reminder.message,
            origin=reminder.origin,
            status=reminder.status,
        )


class TaskDetailResponse(TaskResponse):
    """Detalle de una actividad con sus recordatorios, ordenados por `scheduled_at` (RF-TAR-05)."""

    reminders: list[TaskReminderResponse]


class TaskPageResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


@router.post("", status_code=201, responses={**NOT_FOUND, **INVALID})
def register_task(payload: TaskCreateRequest, user_id: CurrentUserId, service: TaskManagement) -> TaskResponse:
    """Registra una tarea o un examen en una asignatura activa, con su opción de recordatorios (RF-TAR-01, RF-TAR-02)."""

    try:
        task = service.create_task(
            user_id=user_id,
            subject_id=payload.subject_id,
            title=payload.title,
            due_at=payload.due_at,
            type=payload.type.value,
            description=payload.description,
            reminders=payload.reminders.to_plan() if payload.reminders else None,
        )
    except ValueError as error:
        raise _http_error(error) from error
    return TaskResponse.from_data(task)


@router.get("", responses=INVALID)
def list_tasks(
    user_id: CurrentUserId,
    service: TaskManagement,
    subject_id: Annotated[uuid.UUID | None, Query()] = None,
    status: Annotated[
        list[TaskStatus] | None,
        Query(description="Uno o varios estados. `pending` y `overdue` juntos traen las no completadas."),
    ] = None,
    type: Annotated[TaskType | None, Query()] = None,
    due_from: Annotated[datetime | None, Query()] = None,
    due_to: Annotated[datetime | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200, description="Texto en el título, la descripción o el nombre de la asignatura.")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskPageResponse:
    """Lista paginada de las tareas propias, ordenadas por fecha límite (RF-TAR-04)."""

    query = TaskQuery(
        subject_id=subject_id,
        statuses=tuple(status or ()),
        type=type,
        due_from=due_from,
        due_to=due_to,
        text=q,
        limit=limit,
        offset=offset,
    )
    try:
        page = service.list_tasks(user_id, query)
    except ValueError as error:
        raise _http_error(error) from error
    return TaskPageResponse(
        items=[TaskResponse.from_data(task) for task in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{task_id}", responses=NOT_FOUND)
def get_task(task_id: uuid.UUID, user_id: CurrentUserId, service: TaskManagement) -> TaskDetailResponse:
    """Detalle de una tarea con su prioridad, sus fechas y sus recordatorios (RF-TAR-05)."""

    try:
        task, reminders = service.get_task_detail(task_id, user_id)
    except ValueError as error:
        raise _http_error(error) from error
    return TaskDetailResponse(
        **TaskResponse.from_data(task).model_dump(),
        reminders=[TaskReminderResponse.from_view(reminder) for reminder in reminders],
    )


@router.patch("/{task_id}", responses={**NOT_FOUND, **INVALID})
def update_task(
    task_id: uuid.UUID, payload: TaskUpdateRequest, user_id: CurrentUserId, service: TaskManagement
) -> TaskResponse:
    """Actualiza una tarea propia (RF-TAR-06)."""

    try:
        task = service.update_task(
            task_id=task_id,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            subject_id=payload.subject_id,
            type=payload.type.value if payload.type else None,
            due_at=payload.due_at,
        )
    except ValueError as error:
        raise _http_error(error) from error
    return TaskResponse.from_data(task)


@router.patch("/{task_id}/complete", responses=NOT_FOUND)
def complete_task(task_id: uuid.UUID, user_id: CurrentUserId, service: TaskManagement) -> TaskResponse:
    """Marca como completada una tarea propia (RF-TAR-07)."""

    try:
        return TaskResponse.from_data(service.complete_task(task_id, user_id))
    except ValueError as error:
        raise _http_error(error) from error


@router.patch("/{task_id}/reopen", responses=NOT_FOUND)
def reopen_task(task_id: uuid.UUID, user_id: CurrentUserId, service: TaskManagement) -> TaskResponse:
    """Desmarca una tarea completada por error (RF-TAR-08)."""

    try:
        return TaskResponse.from_data(service.reopen_task(task_id, user_id))
    except ValueError as error:
        raise _http_error(error) from error


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_task(task_id: uuid.UUID, user_id: CurrentUserId, service: TaskManagement) -> None:
    """Elimina lógicamente una tarea propia (RF-TAR-10)."""

    try:
        service.delete_task(task_id, user_id)
    except ValueError as error:
        raise _http_error(error) from error
