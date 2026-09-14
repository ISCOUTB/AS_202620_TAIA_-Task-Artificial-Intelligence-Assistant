"""Adaptador HTTP del contexto académico."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskData,
    AcademicTaskManagement,
    get_academic_task_management,
)
from backend.app.modules.academic.application.use_cases.complete_task import TaskNotFoundError
from backend.app.modules.academic.application.use_cases.update_task import TaskNotFoundError as UpdateTaskNotFoundError
from backend.app.shared.adapters.inbound.auth import CurrentUserId

router = APIRouter(prefix="/academic/tasks", tags=["academic"])


def get_task_management() -> AcademicTaskManagement:
    return get_academic_task_management()


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
    status: str

    @classmethod
    def from_data(cls, task: AcademicTaskData) -> "TaskResponse":
        return cls(
            id=task.task_id,
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
    status_code=201,
    responses={422: {"model": ErrorResponse, "description": "Los datos de la tarea no son válidos."}},
)
def register_task(
    payload: TaskCreateRequest,
    user_id: CurrentUserId,
    service: Annotated[AcademicTaskManagement, Depends(get_task_management)],
) -> TaskResponse:
    """Registra una tarea académica para el usuario autenticado."""

    try:
        task = service.create_task(
            user_id=user_id,
            title=payload.title,
            due_date=payload.due_date,
            subject=payload.subject,
            description=payload.description,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return TaskResponse.from_data(task)


@router.get("")
def list_tasks(
    user_id: CurrentUserId,
    service: Annotated[AcademicTaskManagement, Depends(get_task_management)],
) -> list[TaskResponse]:
    """Devuelve únicamente las tareas del usuario autenticado."""

    return [TaskResponse.from_data(task) for task in service.list_tasks(user_id)]


@router.patch(
    "/{task_id}/complete",
    responses={404: {"model": ErrorResponse, "description": "La tarea no existe o no pertenece al usuario."}},
)
def complete_task(
    task_id: uuid.UUID,
    user_id: CurrentUserId,
    service: Annotated[AcademicTaskManagement, Depends(get_task_management)],
) -> TaskResponse:
    """Marca como completada una tarea del usuario autenticado."""

    try:
        task = service.complete_task(task_id=task_id, user_id=user_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return TaskResponse.from_data(task)


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
    service: Annotated[AcademicTaskManagement, Depends(get_task_management)],
) -> TaskResponse:
    """Actualiza una tarea del usuario autenticado."""

    try:
        task = service.update_task(
            task_id=task_id,
            user_id=user_id,
            title=payload.title,
            due_date=payload.due_date,
            subject=payload.subject,
            description=payload.description,
        )
    except UpdateTaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return TaskResponse.from_data(task)
