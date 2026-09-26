"""Modelos ORM del módulo Academic (diccionario de datos, sección 6)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, SmallInteger, String, Time, UniqueConstraint, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.academic.domain.entities.schedule_block import Weekday
from app.modules.academic.domain.entities.task import TaskType
from app.shared.adapters.outbound.database import Base

weekday_enum = Enum(
    Weekday,
    name="weekday",
    values_callable=lambda members: [member.value for member in members],
)

task_type_enum = Enum(
    TaskType,
    name="task_type",
    values_callable=lambda members: [member.value for member in members],
)

# Aún no tienen enumeración de dominio: se agrega en la fase 10 (plan de estudio).
study_plan_status_enum = Enum("proposed", "accepted", "discarded", name="study_plan_status")
study_preference_enum = Enum("between_classes", "after_classes", "both", name="study_preference")


class SubjectModel(Base):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name"),
        CheckConstraint("char_length(trim(name)) > 0", name="name_not_blank"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # Referencia lógica a users.id (otro módulo): sin FOREIGN KEY.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    name: Mapped[str] = mapped_column(String(100))
    normalized_name: Mapped[str] = mapped_column(String(100))
    teacher: Mapped[str | None] = mapped_column(String(100))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[list["SubjectAliasModel"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", order_by="SubjectAliasModel.created_at"
    )


class SubjectAliasModel(Base):
    __tablename__ = "subject_aliases"
    __table_args__ = (UniqueConstraint("subject_id", "normalized_alias"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(50))
    normalized_alias: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScheduleBlockModel(Base):
    __tablename__ = "schedule_blocks"
    __table_args__ = (CheckConstraint("end_time > start_time", name="end_after_start"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[Weekday] = mapped_column(weekday_enum)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    room: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AcademicPeriodModel(Base):
    __tablename__ = "academic_periods"
    __table_args__ = (CheckConstraint("end_date > start_date", name="end_after_start"),)

    # Referencia lógica a users.id (otro módulo): sin FOREIGN KEY.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("char_length(trim(title)) > 0", name="title_not_blank"),
        # Listar por asignatura y ordenar por fecha límite (RF-TAR-04).
        Index(
            "ix_tasks_subject_id_due_at_active",
            "subject_id",
            "due_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # RESTRICT: una asignatura con tareas no se puede borrar, solo archivar (RF-ASG-04).
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    type: Mapped[TaskType] = mapped_column(task_type_enum, server_default=TaskType.TASK.value)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StudyPlanModel(Base):
    """Plan de estudio con las preferencias del formulario (RF-EST-01…03). Cubre 7 días (D-13)."""

    __tablename__ = "study_plans"
    __table_args__ = (
        CheckConstraint(
            "window_start >= '05:00' AND window_end <= '23:00' AND window_end > window_start",
            name="window_within_limits",
        ),
        CheckConstraint("session_minutes > 0", name="session_minutes_positive"),
        # Un solo plan aceptado por usuario.
        Index(
            "uq_study_plans_user_id_accepted",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'accepted'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # Referencia lógica a users.id (otro módulo): sin FOREIGN KEY.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(study_plan_status_enum, server_default="proposed")
    preference: Mapped[str] = mapped_column(study_preference_enum)
    window_start: Mapped[time] = mapped_column(Time, server_default=text("'06:00'"))
    window_end: Mapped[time] = mapped_column(Time, server_default=text("'22:00'"))
    session_minutes: Mapped[int] = mapped_column(SmallInteger, server_default=text("60"))
    start_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StudyPlanDayModel(Base):
    """Días disponibles de un plan; sin selección se guardan los 7 (RF-EST-01)."""

    __tablename__ = "study_plan_days"

    study_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), primary_key=True
    )
    weekday: Mapped[Weekday] = mapped_column(weekday_enum, primary_key=True)


class StudyPlanSubjectModel(Base):
    """Asignaturas incluidas en un plan; sin selección se guardan todas las activas (RF-EST-01)."""

    __tablename__ = "study_plan_subjects"

    study_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), primary_key=True
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True)


class StudySessionModel(Base):
    """Sesión de un plan: prepara una tarea o estudia una asignatura (RF-EST-02)."""

    __tablename__ = "study_sessions"
    __table_args__ = (
        CheckConstraint("(task_id IS NULL) <> (subject_id IS NULL)", name="task_xor_subject"),
        CheckConstraint("ends_at > starts_at", name="ends_after_starts"),
        Index("ix_study_sessions_study_plan_id_starts_at", "study_plan_id", "starts_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    study_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_plans.id", ondelete="CASCADE"))
    task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tasks.id"))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
