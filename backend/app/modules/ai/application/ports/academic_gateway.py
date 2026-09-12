"""Puerto de salida hacia el modulo academico.

El modulo de IA nunca toca la base de datos ni arma consultas: pide
operaciones por este contrato, y academico valida y persiste."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.modules.ai.application.dto import (
    NewTask,
    TaskChanges,
    TaskFilters,
    TaskView,
)


class AcademicError(RuntimeError):
    """Fallo al hablar con el modulo academico."""


class TaskDataRejected(AcademicError):
    """Academico rechazo los datos por una regla de negocio."""


class AcademicGateway(ABC):
    """Operaciones academicas que el asistente puede pedir para un estudiante.

    Toda operacion recibe `user_id` y solo afecta a ese estudiante."""

    @abstractmethod
    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        ...

    @abstractmethod
    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        ...

    @abstractmethod
    def update_task(
        self, user_id: str, task_id: str, changes: TaskChanges
    ) -> TaskView:
        ...
