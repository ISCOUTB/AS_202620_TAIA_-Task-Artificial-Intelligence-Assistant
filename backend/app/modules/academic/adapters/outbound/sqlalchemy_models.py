"""Modelos ORM del módulo Academic (diccionario de datos, sección 6)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, String, Time, UniqueConstraint, Uuid, func, text
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
