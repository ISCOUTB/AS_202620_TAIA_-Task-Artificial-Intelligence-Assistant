"""Modelos ORM del módulo Reminders (diccionario de datos, sección 7).

Todavía no tienen repositorio: el módulo sigue en memoria hasta las fases 5 y 6.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, SmallInteger, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.adapters.outbound.database import Base

reminder_origin_enum = Enum("automatic", "custom", name="reminder_origin")
reminder_status_enum = Enum("pending", "sent", "cancelled", name="reminder_status")


class ReminderModel(Base):
    """Recordatorio programado de una tarea (RF-REC-01…07)."""

    __tablename__ = "reminders"
    __table_args__ = (
        # Lo usa el proceso de envío para encontrar los recordatorios que ya tocan (RF-NOT-02).
        Index("ix_reminders_scheduled_at_pending", "scheduled_at", postgresql_where=text("status = 'pending'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # Referencias lógicas a users.id y tasks.id (otros módulos): sin FOREIGN KEY.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    custom_message: Mapped[str | None] = mapped_column(String(500))
    origin: Mapped[str] = mapped_column(reminder_origin_enum)
    status: Mapped[str] = mapped_column(reminder_status_enum, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificationModel(Base):
    """Notificación generada por un recordatorio; una como máximo por recordatorio (RF-NOT-02…04)."""

    __tablename__ = "notifications"
    __table_args__ = (CheckConstraint("push_attempts BETWEEN 0 AND 4", name="push_attempts_range"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    reminder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reminders.id", ondelete="RESTRICT"), unique=True)
    message: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    push_attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    push_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
