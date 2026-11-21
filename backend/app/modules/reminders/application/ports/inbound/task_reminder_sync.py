"""Puerto de entrada de Reminders para mantener los recordatorios coherentes.

Academic lo llama cuando cambia el ciclo de vida de una actividad (RF-REC-06,
RF-TAR-02, 06, 07, 08 y 10) y Usuario lo llama al desactivar una cuenta
(RF-USR-09). Ningún otro módulo escribe la tabla `reminders`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

ReminderMode = Literal["none", "default", "custom"]


@dataclass(frozen=True)
class ReminderPlan:
    """Opción de recordatorios elegida al crear una actividad (RF-TAR-02).

    - `none`: sin recordatorios.
    - `default`: política por defecto (RF-REC-02).
    - `custom`: las fechas de `custom_at`, con zona horaria (RT-03).
    """

    mode: ReminderMode = "default"
    custom_at: tuple[datetime, ...] = field(default_factory=tuple)


class TaskReminderSync(Protocol):
    """Contrato público de Reminders para el ciclo de vida de las actividades."""

    def on_task_created(
        self, user_id: UUID, task_id: UUID, due_at: datetime, plan: ReminderPlan
    ) -> None:
        """Genera los recordatorios de una actividad nueva según `plan`."""
        ...

    def on_due_changed(self, user_id: UUID, task_id: UUID, due_at: datetime) -> None:
        """Recalcula los automáticos pendientes y cancela los personalizados posteriores."""
        ...

    def on_task_closed(self, user_id: UUID, task_id: UUID) -> None:
        """Cancela los pendientes de una actividad completada o eliminada."""
        ...

    def on_task_reopened(self, user_id: UUID, task_id: UUID, due_at: datetime) -> None:
        """Regenera los automáticos futuros de una actividad reabierta (RF-TAR-08)."""
        ...

    def cancel_all_for_user(self, user_id: UUID) -> None:
        """Cancela todos los pendientes de un usuario que desactiva su cuenta."""
        ...


@dataclass(frozen=True)
class TaskReminderView:
    """Recordatorio publicado para el detalle de una actividad (RF-TAR-05)."""

    reminder_id: UUID
    scheduled_at: datetime
    message: str
    origin: str
    status: str


class TaskReminderReader(Protocol):
    """Contrato público de Reminders para leer los recordatorios de una actividad."""

    def list_for_task(self, user_id: UUID, task_id: UUID) -> list[TaskReminderView]:
        """Recordatorios de la actividad, ordenados por `scheduled_at`."""
        ...


_service: TaskReminderSync | None = None
_reader: TaskReminderReader | None = None


def configure_task_reminder_reader(reader: TaskReminderReader) -> None:
    global _reader
    _reader = reader


def get_task_reminder_reader() -> TaskReminderReader:
    if _reader is None:
        raise RuntimeError("La lectura de recordatorios no ha sido configurada.")
    return _reader


def configure_task_reminder_sync(service: TaskReminderSync) -> None:
    global _service
    _service = service


def get_task_reminder_sync() -> TaskReminderSync:
    if _service is None:
        raise RuntimeError("La sincronización de recordatorios no ha sido configurada.")
    return _service
