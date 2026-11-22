"""Calendario académico: actividades por fecha límite y clases proyectadas (RF-TAR-11, RF-AGT-13).

Los bloques de horario son semanales (RF-ASG-06). Aquí se proyectan en cada fecha
del rango, en hora de Colombia, y solo dentro del período académico si el usuario
lo definió (RF-ASG-08). Los bloques de asignaturas archivadas no se muestran
(RF-ASG-05).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.modules.academic.application.errors import InvalidCalendarRangeError
from app.modules.academic.application.ports.inbound.academic_insights import ClassOccurrence
from app.modules.academic.application.ports.inbound.task_management import AcademicTaskData
from app.modules.academic.application.ports.outbound.academic_period_repository import (
    AcademicPeriodRepository,
)
from app.modules.academic.application.ports.outbound.schedule_block_repository import (
    ScheduleBlockRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from app.modules.academic.application.services.task_management import to_task_data
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.shared.clock import BOGOTA_TZ, Clock, as_bogota, now_bogota

MAX_CALENDAR_DAYS = 31


@dataclass(frozen=True)
class AcademicCalendar:
    """Eventos del usuario entre `start` y `end`, ambos días incluidos."""

    start: date
    end: date
    tasks: list[AcademicTaskData]
    classes: list[ClassOccurrence]


class AcademicCalendarUseCase:
    def __init__(
        self,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        blocks: ScheduleBlockRepository,
        periods: AcademicPeriodRepository,
        clock: Clock | None = None,
    ) -> None:
        self._tasks = tasks
        self._subjects = subjects
        self._blocks = blocks
        self._periods = periods
        self._now = clock or now_bogota

    def calendar(self, user_id: uuid.UUID, start: date, end: date) -> AcademicCalendar:
        """Actividades (tareas y exámenes) que vencen en el rango y clases de cada día (RF-TAR-11).

        El rango incluye los dos días y abarca como máximo `MAX_CALENDAR_DAYS` días.
        """

        if end < start:
            raise InvalidCalendarRangeError("La fecha final del calendario no puede ser anterior a la inicial.")
        if (end - start).days + 1 > MAX_CALENDAR_DAYS:
            raise InvalidCalendarRangeError(
                f"El rango del calendario abarca como máximo {MAX_CALENDAR_DAYS} días."
            )
        range_start = _day_start(start)
        range_end = _day_start(end + timedelta(days=1))
        names = {s.id: s.name for s in self._subjects.list_by_user(user_id, include_archived=True)}
        now = self._now()
        tasks = [
            to_task_data(task, user_id, names.get(task.subject_id, ""), now)
            for task in self._tasks.list_due_between(user_id, range_start, range_end)
        ]
        return AcademicCalendar(start, end, tasks, self.classes(user_id, range_start, range_end))

    def classes(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[ClassOccurrence]:
        """Clases que se cruzan con `[start, end)`, ordenadas por inicio (RF-AGT-13)."""

        start, end = as_bogota(start), as_bogota(end)
        if end <= start:
            raise InvalidCalendarRangeError("El final del rango debe ser posterior al inicio.")
        blocks = self._blocks.list_by_user(user_id)
        if not blocks:
            return []
        names = {s.id: s.name for s in self._subjects.list_by_user(user_id)}
        period = self._periods.get(user_id)
        occurrences = [
            occurrence
            for day in _days(start.date(), end.date())
            if period is None or period.start_date <= day <= period.end_date
            for occurrence in _project(day, blocks, names)
            if occurrence.starts_at < end and occurrence.ends_at > start
        ]
        return sorted(occurrences, key=lambda occurrence: occurrence.starts_at)


def _days(first: date, last: date) -> Iterator[date]:
    day = first
    while day <= last:
        yield day
        day += timedelta(days=1)


def _project(day: date, blocks: list[ScheduleBlock], names: dict[uuid.UUID, str]) -> list[ClassOccurrence]:
    """Bloques del día de la semana de `day`, como clases con fecha y hora de Colombia."""

    weekday = list(Weekday)[day.weekday()]
    return [
        ClassOccurrence(
            subject_id=block.subject_id,
            subject_name=names.get(block.subject_id, ""),
            starts_at=datetime.combine(day, block.start_time, tzinfo=BOGOTA_TZ),
            ends_at=datetime.combine(day, block.end_time, tzinfo=BOGOTA_TZ),
            room=block.room,
        )
        for block in blocks
        if block.weekday is weekday
    ]


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time(0, 0), tzinfo=BOGOTA_TZ)
