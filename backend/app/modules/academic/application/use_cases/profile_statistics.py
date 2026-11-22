"""Estadísticas del perfil, ya agregadas para los gráficos del cliente (RF-PRF-01).

Los períodos se calculan en hora de Colombia (RT-03): la semana va de lunes a
domingo y el mes, del día 1 al último. Las actividades eliminadas no cuentan; las
de asignaturas archivadas sí. Los textos de los gráficos son del cliente.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum

from app.modules.academic.application.errors import AcademicPeriodNotFoundError
from app.modules.academic.application.ports.inbound.task_management import AcademicTaskData
from app.modules.academic.application.ports.outbound.academic_period_repository import (
    AcademicPeriodRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from app.modules.academic.application.services.task_management import to_task_data
from app.modules.academic.domain.entities.task import TaskStatus
from app.shared.clock import BOGOTA_TZ, Clock, now_bogota

WEEKS_OF_HISTORY = 8
UPCOMING_WINDOW = timedelta(days=7)


class StatisticsPeriod(str, Enum):
    WEEK = "week"
    MONTH = "month"
    ACADEMIC_PERIOD = "academic_period"


@dataclass(frozen=True)
class WeeklyCompletion:
    week_start: date
    completed: int


@dataclass(frozen=True)
class OnTimeCompletion:
    """`completed_at <= due_at` entre las completadas del período (RF-PRF-01)."""

    completed: int
    on_time: int
    percentage: float | None


@dataclass(frozen=True)
class SubjectLoad:
    subject_id: uuid.UUID
    subject_name: str
    pending: int


@dataclass(frozen=True)
class ProfileStatistics:
    period: StatisticsPeriod
    start: date
    end: date
    by_status: dict[TaskStatus, int]
    completed_by_week: list[WeeklyCompletion]
    on_time: OnTimeCompletion
    pending_by_subject: list[SubjectLoad]
    upcoming: list[AcademicTaskData]


class ProfileStatisticsUseCase:
    def __init__(
        self,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        periods: AcademicPeriodRepository,
        clock: Clock | None = None,
    ) -> None:
        self._tasks = tasks
        self._subjects = subjects
        self._periods = periods
        self._now = clock or now_bogota

    def statistics(self, user_id: uuid.UUID, period: StatisticsPeriod) -> ProfileStatistics:
        now = self._now()
        first, last = self._period_days(user_id, period, now.date())
        tasks = self._tasks.list_due_between(user_id, _day_start(first), _day_start(last + timedelta(days=1)))
        names = {s.id: s.name for s in self._subjects.list_by_user(user_id, include_archived=True)}

        by_status = dict.fromkeys(TaskStatus, 0)
        load: dict[uuid.UUID, int] = {}
        for task in tasks:
            by_status[task.status(now)] += 1
            if task.completed_at is None:
                load[task.subject_id] = load.get(task.subject_id, 0) + 1
        completed = [task for task in tasks if task.completed_at is not None]
        on_time = sum(1 for task in completed if task.completed_at <= task.due_at)

        return ProfileStatistics(
            period=period,
            start=first,
            end=last,
            by_status=by_status,
            completed_by_week=self._completed_by_week(user_id, now.date()),
            on_time=OnTimeCompletion(
                completed=len(completed),
                on_time=on_time,
                percentage=round(on_time * 100 / len(completed), 1) if completed else None,
            ),
            pending_by_subject=sorted(
                (SubjectLoad(subject_id, names.get(subject_id, ""), count) for subject_id, count in load.items()),
                key=lambda item: (-item.pending, item.subject_name),
            ),
            upcoming=[
                to_task_data(task, user_id, names.get(task.subject_id, ""), now)
                for task in self._tasks.list_due_between(user_id, now, now + UPCOMING_WINDOW)
                if task.completed_at is None
            ],
        )

    def _period_days(self, user_id: uuid.UUID, period: StatisticsPeriod, today: date) -> tuple[date, date]:
        if period is StatisticsPeriod.WEEK:
            monday = today - timedelta(days=today.weekday())
            return monday, monday + timedelta(days=6)
        if period is StatisticsPeriod.MONTH:
            first = today.replace(day=1)
            next_month = (first + timedelta(days=32)).replace(day=1)
            return first, next_month - timedelta(days=1)
        academic = self._periods.get(user_id)
        if academic is None:
            raise AcademicPeriodNotFoundError("No has definido un período académico.")
        return academic.start_date, academic.end_date

    def _completed_by_week(self, user_id: uuid.UUID, today: date) -> list[WeeklyCompletion]:
        """Completadas en cada una de las últimas 8 semanas, de lunes a domingo, la actual incluida."""

        current_monday = today - timedelta(days=today.weekday())
        mondays = [current_monday - timedelta(weeks=weeks) for weeks in range(WEEKS_OF_HISTORY - 1, -1, -1)]
        counts = dict.fromkeys(mondays, 0)
        completed = self._tasks.list_completed_between(
            user_id, _day_start(mondays[0]), _day_start(current_monday + timedelta(weeks=1))
        )
        for task in completed:
            day = task.completed_at.astimezone(BOGOTA_TZ).date()
            counts[day - timedelta(days=day.weekday())] += 1
        return [WeeklyCompletion(monday, counts[monday]) for monday in mondays]


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time(0, 0), tzinfo=BOGOTA_TZ)
