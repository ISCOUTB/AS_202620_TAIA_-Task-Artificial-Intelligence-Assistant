"""Pruebas de integración del esquema completo contra PostgreSQL (docs/diccionario_datos.md).

Verifican que existan todas las tablas y ENUM del diccionario y las
restricciones de las tablas que todavía no tienen repositorio.
Usan la fixture `clean_db` de conftest.py; sin TEST_DATABASE_URL se omiten.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError

from app.modules.academic.adapters.outbound.sqlalchemy_models import (
    StudyPlanDayModel,
    StudyPlanModel,
    StudyPlanSubjectModel,
    StudySessionModel,
    SubjectModel,
)
from app.modules.ai.adapters.outbound.sqlalchemy_models import ConversationMessageModel, ConversationModel
from app.modules.academic.domain.entities.schedule_block import Weekday
from app.modules.reminders.adapters.outbound.sqlalchemy_models import NotificationModel, ReminderModel
from app.modules.usuario.adapters.outbound.sqlalchemy_models import (
    FailedLoginAttemptModel,
    RefreshTokenModel,
    SessionModel,
)
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import UserModel
from app.shared.clock import BOGOTA_TZ

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=BOGOTA_TZ)

DICTIONARY_TABLES = {
    "users", "sessions", "refresh_tokens", "password_reset_tokens", "telegram_link_codes",
    "failed_login_attempts", "subjects", "subject_aliases", "academic_periods", "schedule_blocks",
    "tasks", "study_plans", "study_plan_days", "study_plan_subjects", "study_sessions",
    "reminders", "notifications", "conversations", "conversation_messages",
}
DICTIONARY_ENUMS = {
    "task_type", "weekday", "reminder_origin", "reminder_status",
    "study_plan_status", "study_preference", "message_role",
}


def _insert(session_factory, *models):
    with session_factory.begin() as session:
        session.add_all(models)


def _user(session_factory) -> uuid.UUID:
    user_id = uuid.uuid4()
    _insert(session_factory, UserModel(id=user_id, full_name="Ana", email=f"{user_id.hex}@example.com", password_hash="h"))
    return user_id


def test_schema_has_every_table_and_enum_of_the_dictionary(clean_db):
    with clean_db() as session:
        tables = set(session.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")))
        enums = set(session.scalars(text("SELECT typname FROM pg_type WHERE typtype = 'e'")))

    assert tables - {"alembic_version"} == DICTIONARY_TABLES
    assert enums == DICTIONARY_ENUMS


def test_refresh_tokens_are_deleted_with_their_session(clean_db):
    user_id = _user(clean_db)
    session_id = uuid.uuid4()
    _insert(clean_db, SessionModel(id=session_id, user_id=user_id, fcm_token="token-1"))
    _insert(clean_db, RefreshTokenModel(id=uuid.uuid4(), session_id=session_id, token_hash="a" * 64,
                                        expires_at=datetime.now(BOGOTA_TZ) + timedelta(days=30)))

    with clean_db.begin() as session:
        session.execute(delete(SessionModel).where(SessionModel.id == session_id))
    with clean_db() as session:
        assert session.scalar(text("SELECT count(*) FROM refresh_tokens")) == 0


def test_fcm_token_belongs_to_a_single_session(clean_db):
    user_id = _user(clean_db)
    _insert(clean_db, SessionModel(id=uuid.uuid4(), user_id=user_id, fcm_token="same"))

    with pytest.raises(IntegrityError):
        _insert(clean_db, SessionModel(id=uuid.uuid4(), user_id=user_id, fcm_token="same"))


def test_refresh_token_must_expire_after_creation(clean_db):
    user_id = _user(clean_db)
    session_id = uuid.uuid4()
    _insert(clean_db, SessionModel(id=session_id, user_id=user_id))

    with pytest.raises(IntegrityError):
        _insert(clean_db, RefreshTokenModel(id=uuid.uuid4(), session_id=session_id, token_hash="b" * 64,
                                            expires_at=datetime(2000, 1, 1, tzinfo=BOGOTA_TZ)))


def test_failed_login_attempts_do_not_require_existing_user(clean_db):
    _insert(clean_db, FailedLoginAttemptModel(email="nadie@example.com"))


def _plan(user_id: uuid.UUID, status: str = "proposed", **kwargs) -> StudyPlanModel:
    return StudyPlanModel(id=uuid.uuid4(), user_id=user_id, status=status, preference="both",
                          start_date=date(2026, 10, 1), **kwargs)


def test_only_one_accepted_study_plan_per_user(clean_db):
    user_id = uuid.uuid4()
    _insert(clean_db, _plan(user_id, "accepted"), _plan(user_id, "discarded"), _plan(user_id))

    with pytest.raises(IntegrityError):
        _insert(clean_db, _plan(user_id, "accepted"))


def test_study_plan_window_limits(clean_db):
    with pytest.raises(IntegrityError):
        _insert(clean_db, _plan(uuid.uuid4(), window_start=time(3, 0)))


def test_study_plan_defaults_and_children(clean_db):
    user_id = uuid.uuid4()
    subject = SubjectModel(id=uuid.uuid4(), user_id=user_id, name="Física", normalized_name="fisica")
    plan = _plan(user_id)
    _insert(clean_db, subject, plan)
    _insert(
        clean_db,
        StudyPlanDayModel(study_plan_id=plan.id, weekday=Weekday.MONDAY),
        StudyPlanSubjectModel(study_plan_id=plan.id, subject_id=subject.id),
        StudySessionModel(id=uuid.uuid4(), study_plan_id=plan.id, subject_id=subject.id,
                          starts_at=NOW, ends_at=NOW + timedelta(hours=1)),
    )

    with clean_db() as session:
        stored = session.get(StudyPlanModel, plan.id)
        assert (stored.window_start, stored.window_end, stored.session_minutes) == (time(6), time(22), 60)
    with clean_db.begin() as session:
        session.execute(delete(StudyPlanModel).where(StudyPlanModel.id == plan.id))
    with clean_db() as session:
        counts = [session.scalar(text(f"SELECT count(*) FROM {t}")) for t in
                  ("study_plan_days", "study_plan_subjects", "study_sessions")]
    assert counts == [0, 0, 0]


def test_study_session_targets_exactly_one_of_task_or_subject(clean_db):
    user_id = uuid.uuid4()
    plan = _plan(user_id)
    _insert(clean_db, plan)

    with pytest.raises(IntegrityError):
        _insert(clean_db, StudySessionModel(id=uuid.uuid4(), study_plan_id=plan.id,
                                            starts_at=NOW, ends_at=NOW + timedelta(hours=1)))


def _reminder() -> ReminderModel:
    return ReminderModel(id=uuid.uuid4(), user_id=uuid.uuid4(), task_id=uuid.uuid4(),
                         scheduled_at=NOW, origin="automatic")


def test_one_notification_per_reminder_and_sent_reminders_are_kept(clean_db):
    reminder = _reminder()
    _insert(clean_db, reminder)
    _insert(clean_db, NotificationModel(id=uuid.uuid4(), reminder_id=reminder.id, message="Recuerda"))

    with clean_db() as session:
        assert session.get(ReminderModel, reminder.id).status == "pending"
    with pytest.raises(IntegrityError):
        _insert(clean_db, NotificationModel(id=uuid.uuid4(), reminder_id=reminder.id, message="Otra"))
    with pytest.raises(IntegrityError):
        with clean_db.begin() as session:
            session.execute(delete(ReminderModel).where(ReminderModel.id == reminder.id))


def test_push_attempts_range(clean_db):
    reminder = _reminder()
    _insert(clean_db, reminder)

    with pytest.raises(IntegrityError):
        _insert(clean_db, NotificationModel(id=uuid.uuid4(), reminder_id=reminder.id, message="x", push_attempts=5))


def test_conversation_pending_action_and_messages(clean_db):
    user_id = uuid.uuid4()
    _insert(clean_db, ConversationModel(user_id=user_id, pending_action={"kind": "create_task"},
                                        pending_action_expires_at=NOW))
    _insert(clean_db, ConversationMessageModel(user_id=user_id, role="user", content="Hola"))

    with pytest.raises(IntegrityError):
        _insert(clean_db, ConversationModel(user_id=uuid.uuid4(), pending_action={"kind": "x"}))
    with clean_db.begin() as session:
        session.execute(delete(ConversationModel).where(ConversationModel.user_id == user_id))
    with clean_db() as session:
        assert session.scalar(text("SELECT count(*) FROM conversation_messages")) == 0
