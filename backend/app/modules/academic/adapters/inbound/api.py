"""Adaptador HTTP del contexto académico."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.modules.academic.adapters.outbound.repository_provider import get_task_repository
from backend.app.modules.academic.application.use_cases.complete_task import (
    CompleteTaskUseCase,
    TaskNotFoundError,
)
from backend.app.modules.academic.application.use_cases.list_tasks import ListTasksUseCase
from backend.app.modules.academic.application.use_cases.register_task import RegisterTaskUseCase
from backend.app.modules.academic.application.use_cases.update_task import UpdateTaskUseCase, TaskNotFoundError as UpdateTaskNotFoundError
from backend.app.modules.academic.domain.entities.task import InvalidTaskError, Task, TaskStatus
from backend.app.modules.usuario.adapters.inbound.api import get_authenticated_user_id

router = APIRouter(prefix="/academic/tasks", tags=["academic"])

_repository = get_task_repository()
CurrentUserId = Annotated[uuid.UUID, Depends(get_authenticated_user_id)]


class TaskCreateRequest(BaseModel):
    """Esquema de entrada para registrar una tarea académica."""

    title: str = Field(..., min_length=1, max_length=200)
    due_date: date
    subject: str | None = None
    description: str | None = None


class TaskResponse(BaseModel):
    """Esquema de salida de una tarea académica."""

    id: uuid.UUID
    title: str
    due_date: date
    subject: str | None
    description: str | None
    status: TaskStatus

    @classmethod
    def from_domain(cls, task: Task) -> "TaskResponse":
        return cls(
            id=task.id,
            title=task.title,
            due_date=task.due_date,
            subject=task.subject,
            description=task.description,
            status=task.status,
        )


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por el adaptador cuando la petición falla."""

    detail: str


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse, "description": "Los datos de la tarea no son válidos."}},
)
def register_task(
    payload: TaskCreateRequest,
    user_id: CurrentUserId,
) -> TaskResponse:
    """Registra una tarea académica para el usuario autenticado."""

    use_case = RegisterTaskUseCase(_repository)
    try:
        task = use_case.execute(
            user_id=user_id,
            title=payload.title,
            due_date=payload.due_date,
            subject=payload.subject,
            description=payload.description,
        )
    except InvalidTaskError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return TaskResponse.from_domain(task)


@router.get("")
def list_tasks(user_id: CurrentUserId) -> list[TaskResponse]:
    """Devuelve únicamente las tareas del usuario autenticado."""

    use_case = ListTasksUseCase(_repository)
    return [TaskResponse.from_domain(task) for task in use_case.execute(user_id)]

@router.patch(
    "/{task_id}/complete",
    responses={404: {"model": ErrorResponse, "description": "La tarea no existe o no pertenece al usuario."}},
)
def complete_task(task_id: uuid.UUID, user_id: CurrentUserId) -> TaskResponse:
    """Marca como completada una tarea del usuario autenticado."""

    use_case = CompleteTaskUseCase(_repository)
    try:
        task = use_case.execute(task_id=task_id, user_id=user_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return TaskResponse.from_domain(task)



class TaskUpdateRequest(BaseModel):
    """Campos opcionales para actualizar una tarea."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_date: date | None = None
    subject: str | None = None
    description: str | None = None


@router.patch(
    "/{task_id}",
    responses={
        404: {"model": ErrorResponse, "description": "La tarea no existe o no pertenece al usuario."},
        422: {"model": ErrorResponse, "description": "Los datos de la tarea no son válidos."},
    },
)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    user_id: CurrentUserId,
) -> TaskResponse:
    """Actualiza una tarea del usuario autenticado."""

    use_case = UpdateTaskUseCase(_repository)
    try:
        task = use_case.execute(
            task_id=task_id,
            user_id=user_id,
            title=payload.title,
            due_date=payload.due_date,
            subject=payload.subject,
            description=payload.description,
        )
    except UpdateTaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidTaskError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return TaskResponse.from_domain(task)
