"""Persistencia en PostgreSQL de asignaturas, horario y período académico."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from app.modules.academic.adapters.outbound.sqlalchemy_models import (
    AcademicPeriodModel,
    ScheduleBlockModel,
    SubjectAliasModel,
    SubjectModel,
)
from app.modules.academic.application.ports.outbound.academic_period_repository import (
    AcademicPeriodRepository,
)
from app.modules.academic.application.ports.outbound.schedule_block_repository import (
    ScheduleBlockRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject, SubjectAlias
from app.shared.clock import as_bogota


class SqlAlchemySubjectRepository(SubjectRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, subject: Subject) -> None:
        with self._session_factory.begin() as session:
            session.add(_subject_to_model(subject))

    def save(self, subject: Subject) -> None:
        with self._session_factory.begin() as session:
            session.merge(_subject_to_model(subject))

    def get(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject | None:
        return self._first(SubjectModel.id == subject_id, SubjectModel.user_id == user_id)

    def get_by_normalized_name(self, user_id: uuid.UUID, normalized_name: str) -> Subject | None:
        return self._first(SubjectModel.user_id == user_id, SubjectModel.normalized_name == normalized_name)

    def list_by_user(self, user_id: uuid.UUID, include_archived: bool = False) -> list[Subject]:
        query = select(SubjectModel).where(SubjectModel.user_id == user_id)
        if not include_archived:
            query = query.where(SubjectModel.archived_at.is_(None))
        with self._session_factory() as session:
            return [_subject_to_domain(model) for model in session.scalars(query.order_by(SubjectModel.normalized_name))]

    def delete(self, subject_id: uuid.UUID) -> None:
        # Los alias y los bloques de horario se eliminan por ON DELETE CASCADE.
        with self._session_factory.begin() as session:
            session.execute(delete(SubjectModel).where(SubjectModel.id == subject_id))

    def _first(self, *conditions) -> Subject | None:
        with self._session_factory() as session:
            model = session.scalars(select(SubjectModel).where(*conditions)).first()
            return _subject_to_domain(model) if model is not None else None


class SqlAlchemyScheduleBlockRepository(ScheduleBlockRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, block: ScheduleBlock) -> None:
        with self._session_factory.begin() as session:
            session.add(_block_to_model(block))

    def save(self, block: ScheduleBlock) -> None:
        with self._session_factory.begin() as session:
            session.merge(_block_to_model(block))

    def get(self, block_id: uuid.UUID, user_id: uuid.UUID) -> ScheduleBlock | None:
        query = (
            select(ScheduleBlockModel)
            .join(SubjectModel, SubjectModel.id == ScheduleBlockModel.subject_id)
            .where(ScheduleBlockModel.id == block_id, SubjectModel.user_id == user_id)
        )
        with self._session_factory() as session:
            model = session.scalars(query).first()
            return _block_to_domain(model) if model is not None else None

    def list_by_user(self, user_id: uuid.UUID, weekday: Weekday | None = None) -> list[ScheduleBlock]:
        query = (
            select(ScheduleBlockModel)
            .join(SubjectModel, SubjectModel.id == ScheduleBlockModel.subject_id)
            .where(SubjectModel.user_id == user_id, SubjectModel.archived_at.is_(None))
        )
        if weekday is not None:
            query = query.where(ScheduleBlockModel.weekday == weekday)
        # El ENUM weekday se ordena de lunes a domingo por su orden de declaración.
        query = query.order_by(ScheduleBlockModel.weekday, ScheduleBlockModel.start_time)
        with self._session_factory() as session:
            return [_block_to_domain(model) for model in session.scalars(query)]

    def list_by_subject(self, subject_id: uuid.UUID) -> list[ScheduleBlock]:
        query = select(ScheduleBlockModel).where(ScheduleBlockModel.subject_id == subject_id)
        with self._session_factory() as session:
            return [_block_to_domain(model) for model in session.scalars(query)]

    def delete(self, block_id: uuid.UUID) -> None:
        with self._session_factory.begin() as session:
            session.execute(delete(ScheduleBlockModel).where(ScheduleBlockModel.id == block_id))


class SqlAlchemyAcademicPeriodRepository(AcademicPeriodRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def get(self, user_id: uuid.UUID) -> AcademicPeriod | None:
        with self._session_factory() as session:
            model = session.get(AcademicPeriodModel, user_id)
            if model is None:
                return None
            return AcademicPeriod(user_id=model.user_id, start_date=model.start_date, end_date=model.end_date)

    def save(self, period: AcademicPeriod) -> None:
        with self._session_factory.begin() as session:
            session.merge(
                AcademicPeriodModel(user_id=period.user_id, start_date=period.start_date, end_date=period.end_date)
            )


def _subject_to_model(subject: Subject) -> SubjectModel:
    return SubjectModel(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        normalized_name=subject.normalized_name,
        teacher=subject.teacher,
        archived_at=subject.archived_at,
        created_at=subject.created_at,
        aliases=[
            SubjectAliasModel(
                id=alias.id,
                subject_id=subject.id,
                alias=alias.alias,
                normalized_alias=alias.normalized_alias,
            )
            for alias in subject.aliases
        ],
    )


def _subject_to_domain(model: SubjectModel) -> Subject:
    return Subject(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        normalized_name=model.normalized_name,
        teacher=model.teacher,
        archived_at=_bogota(model.archived_at),
        aliases=[
            SubjectAlias(id=alias.id, alias=alias.alias, normalized_alias=alias.normalized_alias)
            for alias in model.aliases
        ],
        created_at=as_bogota(model.created_at),
    )


def _block_to_model(block: ScheduleBlock) -> ScheduleBlockModel:
    return ScheduleBlockModel(
        id=block.id,
        subject_id=block.subject_id,
        weekday=block.weekday,
        start_time=block.start_time,
        end_time=block.end_time,
        room=block.room,
        created_at=block.created_at,
    )


def _block_to_domain(model: ScheduleBlockModel) -> ScheduleBlock:
    return ScheduleBlock(
        id=model.id,
        subject_id=model.subject_id,
        weekday=model.weekday,
        start_time=model.start_time,
        end_time=model.end_time,
        room=model.room,
        created_at=as_bogota(model.created_at),
    )


def _bogota(value: datetime | None) -> datetime | None:
    return as_bogota(value) if value is not None else None
