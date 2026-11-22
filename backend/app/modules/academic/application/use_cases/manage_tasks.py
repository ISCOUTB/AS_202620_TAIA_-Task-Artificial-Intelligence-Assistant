"""Casos de uso de tareas y exámenes (RF-TAR-01…10).

Los recordatorios pertenecen a Reminders: este caso de uso solo le avisa de cada
cambio del ciclo de vida mediante su puerto de entrada `TaskReminderSync`
(RF-TAR-02, 06, 07, 08 y 10; RF-REC-06).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import replace
from datetime import datetime

from app.modules.academic.application.errors import (
    InvalidReminderPlanError,
    SubjectArchivedError,
    SubjectNotFoundError,
    TaskNotFoundError,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery, TaskRepository
from app.modules.academic.domain.entities.task import Task, TaskType
from app.modules.reminders.application.ports.inbound.task_reminder_sync import (
    ReminderPlan,
    TaskReminderSync,
    get_task_reminder_sync,
)
from app.shared.clock import Clock, as_bogota, now_bogota

MAX_PAGE_SIZE = 100
MAX_CUSTOM_REMINDERS = 10

logger = logging.getLogger(__name__)


class ManageTasksUseCase:
    def __init__(
        self,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        clock: Clock | None = None,
        reminders: TaskReminderSync | None = None,
    ) -> None:
        self._tasks = tasks
        self._subjects = subjects
        self._now = clock or now_bogota
        self._reminders = reminders

    def create(
        self,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
        title: str,
        due_at: datetime,
        type: TaskType = TaskType.TASK,
        description: str | None = None,
        reminders: ReminderPlan | None = None,
    ) -> Task:
        """Sin opción de recordatorios se aplica la política por defecto (RF-TAR-02, RF-AGT-07)."""

        self._ensure_active_subject(subject_id, user_id)
        now = self._now()
        task = Task.create(subject_id, title, due_at, type, description, now=now)
        plan = _checked_plan(reminders or ReminderPlan(), task.due_at, now)
        self._tasks.add(task)
        if (sync := self._sync()) is not None:
            sync.on_task_created(user_id, task.id, task.due_at, plan)
        return task

    def list(self, user_id: uuid.UUID, query: TaskQuery) -> tuple[list[Task], int]:
        if not 1 <= query.limit <= MAX_PAGE_SIZE:
            raise ValueError(f"El tamaño de página debe estar entre 1 y {MAX_PAGE_SIZE}.")
        if query.offset < 0:
            raise ValueError("El desplazamiento no puede ser negativo.")
        return self._tasks.list(user_id, query, self._now())

    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = self._tasks.get(task_id, user_id)
        if task is None:
            raise TaskNotFoundError("La tarea no existe o no pertenece al usuario autenticado.")
        return task

    def update(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        subject_id: uuid.UUID | None = None,
        type: TaskType | None = None,
        due_at: datetime | None = None,
    ) -> Task:
        """Si cambia la fecha límite de una actividad no completada, Reminders recalcula (RF-TAR-06)."""

        task = self.get(task_id, user_id)
        if subject_id is not None and subject_id != task.subject_id:
            self._ensure_active_subject(subject_id, user_id)
        previous_due = task.due_at
        task.update(title, description, subject_id, type, due_at, now=self._now())
        self._tasks.save(task)
        if task.due_at != previous_due and task.completed_at is None and (sync := self._sync()) is not None:
            sync.on_due_changed(user_id, task.id, task.due_at)
        return task

    def complete(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        """Idempotente: completar de nuevo conserva `completed_at` (RF-TAR-07)."""

        task = self.get(task_id, user_id)
        task.complete(self._now())
        self._tasks.save(task)
        if (sync := self._sync()) is not None:
            sync.on_task_closed(user_id, task.id)
        return task

    def reopen(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        """Borra `completed_at` y, si la fecha límite es futura, regenera los automáticos (RF-TAR-08)."""

        task = self.get(task_id, user_id)
        was_completed = task.completed_at is not None
        task.reopen()
        self._tasks.save(task)
        if was_completed and task.due_at > self._now() and (sync := self._sync()) is not None:
            sync.on_task_reopened(user_id, task.id, task.due_at)
        return task

    def delete(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Borrado lógico; Reminders cancela los pendientes (RF-TAR-10)."""

        task = self.get(task_id, user_id)
        task.delete(self._now())
        self._tasks.save(task)
        if (sync := self._sync()) is not None:
            sync.on_task_closed(user_id, task.id)

    def now(self) -> datetime:
        return self._now()

    def _ensure_active_subject(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> None:
        subject = self._subjects.get(subject_id, user_id)
        if subject is None:
            raise SubjectNotFoundError("La asignatura no existe o no pertenece al usuario.")
        if subject.archived:
            raise SubjectArchivedError("La asignatura está archivada y no acepta tareas nuevas.")

    def _sync(self) -> TaskReminderSync | None:
        return self._reminders or _configured_reminder_sync()


def _configured_reminder_sync() -> TaskReminderSync | None:
    """Puerto de Reminders configurado en `main.py` por el frente B.

    Mientras Reminders no esté integrado, el puerto puede no estar configurado:
    se registra un aviso y la actividad queda sin sincronizar (PREGUNTAS P-C-02).
    """

    try:
        return get_task_reminder_sync()
    except RuntimeError:
        logger.warning("La sincronización de recordatorios no está configurada.")
        return None


def _checked_plan(plan: ReminderPlan, due_at: datetime, now: datetime) -> ReminderPlan:
    """Valida la opción antes de guardar la actividad, para no dejarla a medias (RF-TAR-02, RF-REC-01)."""

    if plan.mode != "custom":
        if plan.custom_at:
            raise InvalidReminderPlanError(
                "Las fechas de recordatorio solo se indican con recordatorios personalizados."
            )
        return plan
    if not plan.custom_at:
        raise InvalidReminderPlanError("Indica al menos una fecha para los recordatorios personalizados.")
    if len(plan.custom_at) > MAX_CUSTOM_REMINDERS:
        raise InvalidReminderPlanError(
            f"Los recordatorios personalizados admiten como máximo {MAX_CUSTOM_REMINDERS} fechas."
        )
    moments = tuple(sorted(as_bogota(moment) for moment in plan.custom_at))
    if any(moment <= now or moment >= due_at for moment in moments):
        raise InvalidReminderPlanError(
            "Cada recordatorio debe ser futuro y anterior a la fecha límite de la actividad."
        )
    return replace(plan, custom_at=moments)
