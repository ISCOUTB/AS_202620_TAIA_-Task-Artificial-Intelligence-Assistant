"""Modelos ORM del módulo AI (diccionario de datos, sección 8)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum, ForeignKey, Identity, Index, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.adapters.outbound.database import Base

message_role_enum = Enum("user", "assistant", name="message_role")


class ConversationModel(Base):
    """Estado de la conversación con el agente, una por usuario (RF-AGT-04, RF-AGT-15)."""

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "(pending_action IS NULL) = (pending_action_expires_at IS NULL)",
            name="pending_action_consistent",
        ),
    )

    # Referencia lógica a users.id (otro módulo): sin FOREIGN KEY.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # Objeto de valor PendingAction serializado; la base de datos no lo consulta por dentro.
    pending_action: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    pending_action_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ConversationMessageModel(Base):
    """Mensajes recientes: contexto del agente y conteo del límite de uso (RF-AGT-15, RF-AGT-19)."""

    __tablename__ = "conversation_messages"
    __table_args__ = (Index("ix_conversation_messages_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.user_id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(message_role_enum)
    content: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
