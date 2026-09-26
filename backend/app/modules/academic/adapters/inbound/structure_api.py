"""Adaptador HTTP de asignaturas, horario y período académico (RF-ASG-01…09)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.modules.academic.adapters.outbound.repository_provider import (
    get_academic_period_repository,
    get_schedule_block_repository,
    get_subject_repository,
    get_task_repository,
)
from app.modules.academic.application.errors import (
    AcademicPeriodNotFoundError,
    AliasNotFoundError,
    ScheduleBlockNotFoundError,
    ScheduleOverlapError,
    SubjectAlreadyExistsError,
    SubjectHasTasksError,
    SubjectNotFoundError,
)
from app.modules.academic.application.use_cases.manage_academic_period import (
    ManageAcademicPeriodUseCase,
)
from app.modules.academic.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.modules.academic.application.use_cases.manage_subjects import ManageSubjectsUseCase
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject
from app.shared.adapters.inbound.auth import CurrentUserId

subjects_router = APIRouter(prefix="/academic/subjects", tags=["academic"])
schedule_router = APIRouter(prefix="/academic/schedule-blocks", tags=["academic"])
period_router = APIRouter(prefix="/academic/period", tags=["academic"])


def get_subjects_use_case() -> ManageSubjectsUseCase:
    return ManageSubjectsUseCase(get_subject_repository(), get_schedule_block_repository(), get_task_repository())


def get_schedule_use_case() -> ManageScheduleUseCase:
    return ManageScheduleUseCase(get_subject_repository(), get_schedule_block_repository())


def get_period_use_case() -> ManageAcademicPeriodUseCase:
    return ManageAcademicPeriodUseCase(get_academic_period_repository())


SubjectsUseCase = Annotated[ManageSubjectsUseCase, Depends(get_subjects_use_case)]
ScheduleUseCase = Annotated[ManageScheduleUseCase, Depends(get_schedule_use_case)]
PeriodUseCase = Annotated[ManageAcademicPeriodUseCase, Depends(get_period_use_case)]


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por el adaptador cuando la petición falla."""

    detail: str


NOT_FOUND = {404: {"model": ErrorResponse, "description": "No existe o no pertenece al usuario."}}
INVALID = {422: {"model": ErrorResponse, "description": "Los datos no son válidos."}}
CONFLICT = {409: {"model": ErrorResponse, "description": "Conflicto con datos existentes."}}


def _http_error(error: ValueError) -> HTTPException:
    if isinstance(error, (SubjectNotFoundError, ScheduleBlockNotFoundError, AliasNotFoundError, AcademicPeriodNotFoundError)):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, (SubjectAlreadyExistsError, ScheduleOverlapError, SubjectHasTasksError)):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


# -- asignaturas -------------------------------------------------------------


class SubjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    teacher: str | None = Field(default=None, max_length=100)


class SubjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    teacher: str | None = Field(default=None, max_length=100)


class AliasCreateRequest(BaseModel):
    alias: str = Field(..., min_length=1, max_length=50)


class AliasResponse(BaseModel):
    id: uuid.UUID
    alias: str


class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    teacher: str | None
    archived: bool
    archived_at: datetime | None
    aliases: list[AliasResponse]
    pending_tasks: int
    created_at: datetime

    @classmethod
    def from_domain(cls, subject: Subject, pending_tasks: int) -> "SubjectResponse":
        return cls(
            id=subject.id,
            name=subject.name,
            teacher=subject.teacher,
            archived=subject.archived,
            archived_at=subject.archived_at,
            aliases=[AliasResponse(id=alias.id, alias=alias.alias) for alias in subject.aliases],
            pending_tasks=pending_tasks,
            created_at=subject.created_at,
        )


def _subject_response(subject: Subject, use_case: ManageSubjectsUseCase) -> SubjectResponse:
    return SubjectResponse.from_domain(subject, use_case.pending_task_counts(subject.user_id).get(subject.id, 0))


@subjects_router.post("", status_code=status.HTTP_201_CREATED, responses={**CONFLICT, **INVALID})
def create_subject(payload: SubjectCreateRequest, user_id: CurrentUserId, use_case: SubjectsUseCase) -> SubjectResponse:
    """Registra una asignatura (RF-ASG-01)."""
    try:
        return _subject_response(use_case.create(user_id, payload.name, payload.teacher), use_case)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.get("")
def list_subjects(
    user_id: CurrentUserId,
    use_case: SubjectsUseCase,
    include_archived: Annotated[bool, Query()] = False,
) -> list[SubjectResponse]:
    """Lista las asignaturas del usuario con sus tareas pendientes (RF-ASG-02)."""
    counts = use_case.pending_task_counts(user_id)
    return [
        SubjectResponse.from_domain(subject, counts.get(subject.id, 0))
        for subject in use_case.list(user_id, include_archived)
    ]


@subjects_router.get("/{subject_id}", responses=NOT_FOUND)
def get_subject(subject_id: uuid.UUID, user_id: CurrentUserId, use_case: SubjectsUseCase) -> SubjectResponse:
    """Consulta una asignatura con sus tareas pendientes (RF-ASG-02)."""
    try:
        return _subject_response(use_case.get(subject_id, user_id), use_case)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.patch("/{subject_id}", responses={**NOT_FOUND, **CONFLICT, **INVALID})
def update_subject(
    subject_id: uuid.UUID, payload: SubjectUpdateRequest, user_id: CurrentUserId, use_case: SubjectsUseCase
) -> SubjectResponse:
    """Edita el nombre o el docente (RF-ASG-03)."""
    try:
        return _subject_response(use_case.update(subject_id, user_id, payload.name, payload.teacher), use_case)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, responses={**NOT_FOUND, **CONFLICT})
def delete_subject(subject_id: uuid.UUID, user_id: CurrentUserId, use_case: SubjectsUseCase) -> None:
    """Elimina una asignatura sin actividades, junto con sus bloques de horario (RF-ASG-04)."""
    try:
        use_case.delete(subject_id, user_id)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.post("/{subject_id}/archive", responses=NOT_FOUND)
def archive_subject(subject_id: uuid.UUID, user_id: CurrentUserId, use_case: SubjectsUseCase) -> SubjectResponse:
    """Archiva una asignatura (RF-ASG-05)."""
    try:
        return _subject_response(use_case.archive(subject_id, user_id), use_case)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.post("/{subject_id}/unarchive", responses={**NOT_FOUND, **CONFLICT})
def unarchive_subject(subject_id: uuid.UUID, user_id: CurrentUserId, use_case: SubjectsUseCase) -> SubjectResponse:
    """Desarchiva una asignatura si su horario no choca con el actual (RF-ASG-05)."""
    try:
        return _subject_response(use_case.unarchive(subject_id, user_id), use_case)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.post(
    "/{subject_id}/aliases", status_code=status.HTTP_201_CREATED, responses={**NOT_FOUND, **INVALID}
)
def add_subject_alias(
    subject_id: uuid.UUID, payload: AliasCreateRequest, user_id: CurrentUserId, use_case: SubjectsUseCase
) -> SubjectResponse:
    """Agrega un alias a la asignatura (RF-ASG-09)."""
    try:
        return _subject_response(use_case.add_alias(subject_id, user_id, payload.alias), use_case)
    except ValueError as error:
        raise _http_error(error) from error


@subjects_router.delete("/{subject_id}/aliases/{alias_id}", responses=NOT_FOUND)
def remove_subject_alias(
    subject_id: uuid.UUID, alias_id: uuid.UUID, user_id: CurrentUserId, use_case: SubjectsUseCase
) -> SubjectResponse:
    """Elimina un alias de la asignatura (RF-ASG-09)."""
    try:
        return _subject_response(use_case.remove_alias(subject_id, user_id, alias_id), use_case)
    except ValueError as error:
        raise _http_error(error) from error


# -- horario -------------------------------------------------------------------


class ScheduleBlockCreateRequest(BaseModel):
    subject_id: uuid.UUID
    weekday: Weekday
    start_time: time
    end_time: time
    room: str | None = Field(default=None, max_length=50)


class ScheduleBlockUpdateRequest(BaseModel):
    subject_id: uuid.UUID | None = None
    weekday: Weekday | None = None
    start_time: time | None = None
    end_time: time | None = None
    room: str | None = Field(default=None, max_length=50)


class ScheduleBlockResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    subject_name: str
    weekday: Weekday
    start_time: time
    end_time: time
    room: str | None

    @classmethod
    def from_domain(cls, block: ScheduleBlock, subject_name: str) -> "ScheduleBlockResponse":
        return cls(
            id=block.id,
            subject_id=block.subject_id,
            subject_name=subject_name,
            weekday=block.weekday,
            start_time=block.start_time,
            end_time=block.end_time,
            room=block.room,
        )


def _subject_names(user_id: uuid.UUID, subjects: ManageSubjectsUseCase) -> dict[uuid.UUID, str]:
    return {subject.id: subject.name for subject in subjects.list(user_id, include_archived=True)}


@schedule_router.post("", status_code=status.HTTP_201_CREATED, responses={**NOT_FOUND, **CONFLICT, **INVALID})
def create_schedule_block(
    payload: ScheduleBlockCreateRequest,
    user_id: CurrentUserId,
    use_case: ScheduleUseCase,
    subjects: SubjectsUseCase,
) -> ScheduleBlockResponse:
    """Registra un bloque del horario de clases (RF-ASG-06)."""
    try:
        block = use_case.create(
            user_id, payload.subject_id, payload.weekday, payload.start_time, payload.end_time, payload.room
        )
    except ValueError as error:
        raise _http_error(error) from error
    return ScheduleBlockResponse.from_domain(block, _subject_names(user_id, subjects)[block.subject_id])


@schedule_router.get("")
def list_schedule_blocks(
    user_id: CurrentUserId,
    use_case: ScheduleUseCase,
    subjects: SubjectsUseCase,
    weekday: Annotated[Weekday | None, Query()] = None,
) -> list[ScheduleBlockResponse]:
    """Horario semanal o de un día, ordenado por día y hora (RF-ASG-07)."""
    names = _subject_names(user_id, subjects)
    return [ScheduleBlockResponse.from_domain(block, names[block.subject_id]) for block in use_case.list(user_id, weekday)]


@schedule_router.patch("/{block_id}", responses={**NOT_FOUND, **CONFLICT, **INVALID})
def update_schedule_block(
    block_id: uuid.UUID,
    payload: ScheduleBlockUpdateRequest,
    user_id: CurrentUserId,
    use_case: ScheduleUseCase,
    subjects: SubjectsUseCase,
) -> ScheduleBlockResponse:
    """Edita un bloque de horario (RF-ASG-07)."""
    try:
        block = use_case.update(
            block_id,
            user_id,
            subject_id=payload.subject_id,
            weekday=payload.weekday,
            start_time=payload.start_time,
            end_time=payload.end_time,
            room=payload.room,
        )
    except ValueError as error:
        raise _http_error(error) from error
    return ScheduleBlockResponse.from_domain(block, _subject_names(user_id, subjects)[block.subject_id])


@schedule_router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_schedule_block(block_id: uuid.UUID, user_id: CurrentUserId, use_case: ScheduleUseCase) -> None:
    """Elimina un bloque de horario (RF-ASG-07)."""
    try:
        use_case.delete(block_id, user_id)
    except ValueError as error:
        raise _http_error(error) from error


# -- período académico ---------------------------------------------------------


class AcademicPeriodRequest(BaseModel):
    start_date: date
    end_date: date


class AcademicPeriodResponse(BaseModel):
    start_date: date
    end_date: date

    @classmethod
    def from_domain(cls, period: AcademicPeriod) -> "AcademicPeriodResponse":
        return cls(start_date=period.start_date, end_date=period.end_date)


@period_router.get("", responses=NOT_FOUND)
def get_academic_period(user_id: CurrentUserId, use_case: PeriodUseCase) -> AcademicPeriodResponse:
    """Consulta el período académico vigente (RF-ASG-08)."""
    try:
        return AcademicPeriodResponse.from_domain(use_case.get(user_id))
    except ValueError as error:
        raise _http_error(error) from error


@period_router.put("", responses=INVALID)
def set_academic_period(
    payload: AcademicPeriodRequest, user_id: CurrentUserId, use_case: PeriodUseCase
) -> AcademicPeriodResponse:
    """Define o reemplaza el período académico (RF-ASG-08)."""
    try:
        return AcademicPeriodResponse.from_domain(use_case.set(user_id, payload.start_date, payload.end_date))
    except ValueError as error:
        raise _http_error(error) from error
