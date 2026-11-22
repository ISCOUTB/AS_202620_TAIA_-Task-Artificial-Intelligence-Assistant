"""Adaptador HTTP del calendario académico (RF-TAR-11)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.modules.academic.adapters.inbound.api import ErrorResponse, TaskResponse
from app.modules.academic.application.errors import InvalidCalendarRangeError
from app.modules.academic.application.ports.inbound.academic_insights import ClassOccurrence
from app.modules.academic.adapters.inbound.study_plan_api import StudyPlans, StudySessionResponse
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.shared.adapters.inbound.auth import CurrentUserId
from app.shared.clock import BOGOTA_TZ

router = APIRouter(prefix="/academic/calendar", tags=["academic"])

_calendar: AcademicCalendarUseCase | None = None


def configure_calendar_use_case(calendar: AcademicCalendarUseCase) -> None:
    global _calendar
    _calendar = calendar


def get_calendar_use_case() -> AcademicCalendarUseCase:
    if _calendar is None:
        raise RuntimeError("El calendario académico no está configurado.")
    return _calendar


CalendarUseCase = Annotated[AcademicCalendarUseCase, Depends(get_calendar_use_case)]

INVALID_RANGE = {422: {"model": ErrorResponse, "description": "El rango de fechas está invertido o abarca más de 31 días."}}


class ClassOccurrenceResponse(BaseModel):
    """Un bloque de clase proyectado en una fecha, en hora de Colombia."""

    subject_id: uuid.UUID
    subject_name: str
    starts_at: datetime
    ends_at: datetime
    room: str | None

    @classmethod
    def from_occurrence(cls, occurrence: ClassOccurrence) -> "ClassOccurrenceResponse":
        return cls(
            subject_id=occurrence.subject_id,
            subject_name=occurrence.subject_name,
            starts_at=occurrence.starts_at,
            ends_at=occurrence.ends_at,
            room=occurrence.room,
        )


class CalendarResponse(BaseModel):
    """Eventos del rango: actividades por fecha límite (con `type` para los exámenes), clases y
    sesiones del plan de estudio aceptado (RF-EST-03)."""

    start: date
    end: date
    tasks: list[TaskResponse]
    classes: list[ClassOccurrenceResponse]
    study_sessions: list[StudySessionResponse]


@router.get("", responses=INVALID_RANGE)
def get_calendar(
    user_id: CurrentUserId,
    calendar: CalendarUseCase,
    plans: StudyPlans,
    start: Annotated[date, Query(description="Primer día del rango (AAAA-MM-DD, hora de Colombia).")],
    end: Annotated[date, Query(description="Último día del rango, incluido. Como máximo 31 días contando los dos extremos.")],
) -> CalendarResponse:
    """Actividades, exámenes y clases del usuario entre dos fechas (RF-TAR-11)."""

    try:
        result = calendar.calendar(user_id, start, end)
    except InvalidCalendarRangeError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return CalendarResponse(
        start=result.start,
        end=result.end,
        tasks=[TaskResponse.from_data(task) for task in result.tasks],
        classes=[ClassOccurrenceResponse.from_occurrence(occurrence) for occurrence in result.classes],
        study_sessions=[
            StudySessionResponse(
                id=item.session.id, starts_at=item.session.starts_at, ends_at=item.session.ends_at,
                task_id=item.session.task_id, subject_id=item.session.subject_id,
                title=item.title, subject_name=item.subject_name,
            )
            for item in plans.calendar_sessions(
                user_id,
                datetime.combine(start, time(0, 0), tzinfo=BOGOTA_TZ),
                datetime.combine(end + timedelta(days=1), time(0, 0), tzinfo=BOGOTA_TZ),
            )
        ],
    )
