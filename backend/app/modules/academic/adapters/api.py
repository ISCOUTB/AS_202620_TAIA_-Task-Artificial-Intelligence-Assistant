"""Adaptador de entrada HTTP (API REST) para el módulo `academic`.

Expone el aspecto A-01 mediante FastAPI. Traduce peticiones HTTP a llamadas
a los casos de uso de `application`, y las entidades de dominio a esquemas
Pydantic de salida.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.modules.academic.adapters.in_memory_task_repository import (
    InMemoryTaskRepository,
)
from backend.app.modules.academic.application.list_tasks import ListTasksUseCase
from backend.app.modules.academic.application.register_task import RegisterTaskUseCase
from backend.app.modules.academic.domain.task import InvalidTaskError, Task, TaskStatus

router = APIRouter(prefix="/academic/tasks", tags=["academic"])

# Instancia compartida del adaptador de persistencia para esta entrega.
# Al incorporar PostgreSQL, esta línea se reemplaza por el adaptador real
# sin tocar el router ni los casos de uso.
_repository = InMemoryTaskRepository()


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


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def register_task(payload: TaskCreateRequest) -> TaskResponse:
    """Registra una tarea académica nueva (RF-01)."""

    use_case = RegisterTaskUseCase(_repository)
    try:
        task = use_case.execute(
            title=payload.title,
            due_date=payload.due_date,
            subject=payload.subject,
            description=payload.description,
        )
    except InvalidTaskError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return TaskResponse.from_domain(task)


@router.get("", response_model=list[TaskResponse])
def list_tasks() -> list[TaskResponse]:
    """Devuelve las tareas académicas registradas (RF-02)."""

    use_case = ListTasksUseCase(_repository)
    return [TaskResponse.from_domain(task) for task in use_case.execute()]
