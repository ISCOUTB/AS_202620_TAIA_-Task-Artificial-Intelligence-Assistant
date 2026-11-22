"""Puerto de salida hacia el modulo academico.

El modulo de IA nunca toca la base de datos ni arma consultas: pide
operaciones por este contrato, y academico valida y persiste."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.ai.application.dto import (
    ClassView,
    NewTask,
    PeriodSummary,
    SubjectOption,
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

    Toda operacion recibe `user_id` y solo afecta a ese estudiante. El
    `user_id` sale de la sesion o de la vinculacion de Telegram (RF-AGT-17)."""

    @abstractmethod
    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        ...

    @abstractmethod
    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        """Tareas que cumplen los filtros, ordenadas por fecha limite."""

    @abstractmethod
    def update_task(
        self, user_id: str, task_id: str, changes: TaskChanges
    ) -> TaskView:
        ...

    @abstractmethod
    def complete_task(self, user_id: str, task_id: str) -> TaskView:
        """Marca la tarea como completada (RF-AGT-09)."""

    @abstractmethod
    def match_subjects(self, user_id: str, text: str) -> list[SubjectOption]:
        """Asignaturas del estudiante que coinciden con el texto (RF-AGT-10)."""

    @abstractmethod
    def summarize_period(
        self, user_id: str, start: datetime, end: datetime
    ) -> PeriodSummary:
        """Conteos del periodo `[start, end)` (RF-AGT-12)."""

    @abstractmethod
    def get_classes(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[ClassView]:
        """Clases entre `start` y `end`, ordenadas por inicio (RF-AGT-13)."""
