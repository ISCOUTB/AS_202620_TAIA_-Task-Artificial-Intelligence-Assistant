"""Persistencia en PostgreSQL de los planes de estudio (diccionario de datos §6.6 a §6.10)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.modules.academic.adapters.outbound.sqlalchemy_models import (
    StudyPlanBusyBlockModel,
    StudyPlanDayModel,
    StudyPlanModel,
    StudyPlanSubjectModel,
    StudySessionModel,
)
from app.modules.academic.application.ports.outbound.study_plan_repository import StudyPlanRepository
from app.modules.academic.domain.entities.study_plan import (
    BusyBlock,
    BusyBlockKind,
    StudyPlan,
    StudyPlanStatus,
    StudyPreference,
    StudyPreferences,
    StudySession,
    StudyTimePreference,
)
from app.shared.clock import as_bogota

PROPOSED = StudyPlanStatus.PROPOSED.value
ACCEPTED = StudyPlanStatus.ACCEPTED.value
DISCARDED = StudyPlanStatus.DISCARDED.value


class SqlAlchemyStudyPlanRepository(StudyPlanRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, plan: StudyPlan) -> None:
        prefs = plan.preferences
        with self._session_factory.begin() as session:
            session.execute(
                update(StudyPlanModel)
                .where(StudyPlanModel.user_id == plan.user_id, StudyPlanModel.status == PROPOSED)
                .values(status=DISCARDED)
            )
            session.add(StudyPlanModel(
                id=plan.id,
                user_id=plan.user_id,
                status=plan.status.value,
                preference=prefs.preference.value,
                window_start=prefs.window_start,
                window_end=prefs.window_end,
                session_minutes=prefs.session_minutes,
                max_daily_minutes=prefs.max_daily_minutes,
                preferred_time=prefs.preferred_time.value,
                start_date=plan.start_date,
            ))
            session.flush()
            session.add_all([StudyPlanDayModel(study_plan_id=plan.id, weekday=day) for day in prefs.days])
            session.add_all([
                StudyPlanSubjectModel(study_plan_id=plan.id, subject_id=subject_id) for subject_id in prefs.subject_ids
            ])
            session.add_all([
                StudyPlanBusyBlockModel(
                    id=uuid.uuid4(), study_plan_id=plan.id, kind=block.kind.value, weekday=block.weekday,
                    start_time=block.start_time, end_time=block.end_time,
                )
                for block in prefs.busy_blocks
            ])
            session.add_all([
                StudySessionModel(
                    id=s.id, study_plan_id=plan.id, task_id=s.task_id, subject_id=s.subject_id,
                    starts_at=s.starts_at, ends_at=s.ends_at,
                )
                for s in plan.sessions
            ])

    def get(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> StudyPlan | None:
        with self._session_factory() as session:
            model = session.scalars(
                select(StudyPlanModel).where(StudyPlanModel.id == plan_id, StudyPlanModel.user_id == user_id)
            ).first()
            return _to_domain(session, model) if model is not None else None

    def current(self, user_id: uuid.UUID) -> StudyPlan | None:
        with self._session_factory() as session:
            for status in (PROPOSED, ACCEPTED):
                model = session.scalars(
                    select(StudyPlanModel)
                    .where(StudyPlanModel.user_id == user_id, StudyPlanModel.status == status)
                    .order_by(StudyPlanModel.created_at.desc())
                ).first()
                if model is not None:
                    return _to_domain(session, model)
            return None

    def accept(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        with self._session_factory.begin() as session:
            target = session.scalar(
                select(StudyPlanModel.id)
                .where(StudyPlanModel.id == plan_id, StudyPlanModel.user_id == user_id,
                       StudyPlanModel.status == PROPOSED)
                .with_for_update()
            )
            if target is None:
                return False
            # El índice único parcial exige descartar el aceptado anterior primero.
            session.execute(
                update(StudyPlanModel)
                .where(StudyPlanModel.user_id == user_id, StudyPlanModel.status == ACCEPTED)
                .values(status=DISCARDED)
            )
            session.execute(update(StudyPlanModel).where(StudyPlanModel.id == plan_id).values(status=ACCEPTED))
            return True

    def discard(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        with self._session_factory.begin() as session:
            return session.execute(
                update(StudyPlanModel)
                .where(StudyPlanModel.id == plan_id, StudyPlanModel.user_id == user_id,
                       StudyPlanModel.status != DISCARDED)
                .values(status=DISCARDED)
            ).rowcount == 1

    def accepted_sessions(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[StudySession]:
        query = (
            select(StudySessionModel)
            .join(StudyPlanModel, StudyPlanModel.id == StudySessionModel.study_plan_id)
            .where(
                StudyPlanModel.user_id == user_id,
                StudyPlanModel.status == ACCEPTED,
                StudySessionModel.starts_at >= start,
                StudySessionModel.starts_at < end,
            )
            .order_by(StudySessionModel.starts_at)
        )
        with self._session_factory() as session:
            return [_session_to_domain(model) for model in session.scalars(query)]


def _session_to_domain(model: StudySessionModel) -> StudySession:
    return StudySession(
        id=model.id,
        starts_at=as_bogota(model.starts_at),
        ends_at=as_bogota(model.ends_at),
        task_id=model.task_id,
        subject_id=model.subject_id,
    )


def _to_domain(session: Session, model: StudyPlanModel) -> StudyPlan:
    days = session.scalars(select(StudyPlanDayModel.weekday).where(StudyPlanDayModel.study_plan_id == model.id))
    subjects = session.scalars(
        select(StudyPlanSubjectModel.subject_id).where(StudyPlanSubjectModel.study_plan_id == model.id)
    )
    blocks = session.scalars(
        select(StudyPlanBusyBlockModel)
        .where(StudyPlanBusyBlockModel.study_plan_id == model.id)
        .order_by(StudyPlanBusyBlockModel.weekday, StudyPlanBusyBlockModel.start_time)
    )
    sessions = session.scalars(
        select(StudySessionModel)
        .where(StudySessionModel.study_plan_id == model.id)
        .order_by(StudySessionModel.starts_at)
    )
    preferences = StudyPreferences(
        preference=StudyPreference(model.preference),
        days=frozenset(days),
        window_start=model.window_start,
        window_end=model.window_end,
        session_minutes=model.session_minutes,
        subject_ids=tuple(subjects),
        busy_blocks=tuple(
            BusyBlock(BusyBlockKind(b.kind), b.weekday, b.start_time, b.end_time) for b in blocks
        ),
        max_daily_minutes=model.max_daily_minutes,
        preferred_time=StudyTimePreference(model.preferred_time),
    )
    return StudyPlan(
        id=model.id,
        user_id=model.user_id,
        preferences=preferences,
        start_date=model.start_date,
        sessions=[_session_to_domain(s) for s in sessions],
        status=StudyPlanStatus(model.status),
    )
