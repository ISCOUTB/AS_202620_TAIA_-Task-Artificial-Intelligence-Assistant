"""Adaptador HTTP de las estadísticas del perfil (RF-PRF-01)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.modules.academic.adapters.inbound.api import ErrorResponse, TaskResponse
from app.modules.academic.application.errors import AcademicPeriodNotFoundError
from app.modules.academic.application.use_cases.profile_statistics import (
    ProfileStatisticsUseCase,
    StatisticsPeriod,
)
from app.modules.academic.domain.entities.task import TaskStatus
from app.shared.adapters.inbound.auth import CurrentUserId

router = APIRouter(prefix="/academic/statistics", tags=["academic"])

_statistics: ProfileStatisticsUseCase | None = None


def configure_statistics_use_case(statistics: ProfileStatisticsUseCase) -> None:
    global _statistics
    _statistics = statistics


def get_statistics_use_case() -> ProfileStatisticsUseCase:
    if _statistics is None:
        raise RuntimeError("Las estadísticas del perfil no están configuradas.")
    return _statistics


StatisticsUseCase = Annotated[ProfileStatisticsUseCase, Depends(get_statistics_use_case)]

NO_PERIOD = {404: {"model": ErrorResponse, "description": "Se pidió el período académico y no está definido."}}


class StatusCountsResponse(BaseModel):
    pending: int
    completed: int
    overdue: int


class WeeklyCompletionResponse(BaseModel):
    week_start: date
    completed: int


class OnTimeResponse(BaseModel):
    """Completadas del período y cuántas con `completed_at <= due_at`. Sin completadas, `percentage` es nulo."""

    completed: int
    on_time: int
    percentage: float | None


class SubjectLoadResponse(BaseModel):
    subject_id: uuid.UUID
    subject_name: str
    pending: int


class ProfileStatisticsResponse(BaseModel):
    """Datos agregados de los gráficos del perfil; `start` y `end` son los días del período, ambos incluidos."""

    period: StatisticsPeriod
    start: date
    end: date
    by_status: StatusCountsResponse
    completed_by_week: list[WeeklyCompletionResponse]
    on_time: OnTimeResponse
    pending_by_subject: list[SubjectLoadResponse]
    upcoming: list[TaskResponse]


@router.get("", responses=NO_PERIOD)
def get_profile_statistics(
    user_id: CurrentUserId,
    statistics: StatisticsUseCase,
    period: Annotated[StatisticsPeriod, Query(description="`week`, `month` o `academic_period`, en hora de Colombia.")],
) -> ProfileStatisticsResponse:
    """Estadísticas de rendimiento del período elegido (RF-PRF-01)."""

    try:
        result = statistics.statistics(user_id, period)
    except AcademicPeriodNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ProfileStatisticsResponse(
        period=result.period,
        start=result.start,
        end=result.end,
        by_status=StatusCountsResponse(
            pending=result.by_status[TaskStatus.PENDING],
            completed=result.by_status[TaskStatus.COMPLETED],
            overdue=result.by_status[TaskStatus.OVERDUE],
        ),
        completed_by_week=[
            WeeklyCompletionResponse(week_start=week.week_start, completed=week.completed)
            for week in result.completed_by_week
        ],
        on_time=OnTimeResponse(
            completed=result.on_time.completed, on_time=result.on_time.on_time, percentage=result.on_time.percentage
        ),
        pending_by_subject=[
            SubjectLoadResponse(subject_id=item.subject_id, subject_name=item.subject_name, pending=item.pending)
            for item in result.pending_by_subject
        ],
        upcoming=[TaskResponse.from_data(task) for task in result.upcoming],
    )
