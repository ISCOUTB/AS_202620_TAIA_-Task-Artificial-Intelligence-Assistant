"""Adaptador HTTP de tareas y exámenes (RF-TAR-01, 03…10)."""

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
from app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskData,
    AcademicTaskManagement,
    get_academic_task_management,
)
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery
from app.modules.academic.domain.entities.task import TaskStatus, TaskType
from app.shared.adapters.inbound.auth import CurrentUserId
from app.shared.clock import end_of_day_bogota

router = APIRouter(prefix="/academic/tasks", tags=["academic"])


def get_task_management() -> AcademicTaskManagement:
    return get_academic_task_management()


TaskManagement = Annotated[AcademicTaskManagement, Depends(get_task_management)]


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


class TaskCreateRequest(BaseModel):
    """Esquema de entrada para registrar una tarea o un examen."""

    subject_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=200)
    due_at: DueAt
    type: TaskType = TaskType.TASK
    description: str | None = Field(default=None, max_length=2000)


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


class TaskPageResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


@router.post("", status_code=201, responses={**NOT_FOUND, **INVALID})
def register_task(payload: TaskCreateRequest, user_id: CurrentUserId, service: TaskManagement) -> TaskResponse:
    """Registra una tarea o un examen en una asignatura activa (RF-TAR-01)."""

    try:
        task = service.create_task(
            user_id=user_id,
            subject_id=payload.subject_id,
            title=payload.title,
            due_at=payload.due_at,
            type=payload.type.value,
            description=payload.description,
        )
    except ValueError as error:
        raise _http_error(error) from error
    return TaskResponse.from_data(task)


@router.get("", responses=INVALID)
def list_tasks(
    user_id: CurrentUserId,
    service: TaskManagement,
    subject_id: Annotated[uuid.UUID | None, Query()] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    type: Annotated[TaskType | None, Query()] = None,
    due_from: Annotated[datetime | None, Query()] = None,
    due_to: Annotated[datetime | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200, description="Texto en el título o la descripción.")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskPageResponse:
    """Lista paginada de las tareas propias, ordenadas por fecha límite (RF-TAR-04)."""

    query = TaskQuery(
        subject_id=subject_id,
        status=status,
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
def get_task(task_id: uuid.UUID, user_id: CurrentUserId, service: TaskManagement) -> TaskResponse:
    """Detalle de una tarea (RF-TAR-05)."""

    try:
        return TaskResponse.from_data(service.get_task(task_id, user_id))
    except ValueError as error:
        raise _http_error(error) from error


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
