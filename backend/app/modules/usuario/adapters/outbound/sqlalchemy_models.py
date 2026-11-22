"""Modelos ORM de sesiones, tokens e intentos de acceso (diccionario de datos, 5.2 a 5.7).

La tabla `users` está en sqlalchemy_user_repository.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.adapters.outbound.database import Base

_USERS_ID = "users.id"
_EXPIRES_AFTER_CREATED = "expires_at > created_at"


class SessionModel(Base):
    """Sesión iniciada en un dispositivo; el JWT lleva su id como `sid` (RF-USR-03, 04, RF-NOT-01)."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user_id_active", "user_id", postgresql_where=text("revoked_at IS NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(_USERS_ID))
    fcm_token: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshTokenModel(Base):
    """Tokens de renovación con rotación de un solo uso (RF-USR-03)."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (CheckConstraint(_EXPIRES_AFTER_CREATED, name="expires_after_created"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetTokenModel(Base):
    """Códigos de verificación para recuperar la contraseña (RF-USR-08).

    Sin `UNIQUE (token_hash)`: con 6 dígitos, dos usuarios pueden recibir el mismo código.
    """

    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        CheckConstraint(_EXPIRES_AFTER_CREATED, name="expires_after_created"),
        CheckConstraint("failed_attempts BETWEEN 0 AND 5", name="failed_attempts_range"),
        Index("ix_password_reset_tokens_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(_USERS_ID))
    token_hash: Mapped[str] = mapped_column(CHAR(64))
    failed_attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TelegramLinkCodeModel(Base):
    """Códigos de un solo uso para vincular Telegram (RF-TEL-01)."""

    __tablename__ = "telegram_link_codes"
    __table_args__ = (CheckConstraint(_EXPIRES_AFTER_CREATED, name="expires_after_created"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(_USERS_ID))
    code_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FailedLoginAttemptModel(Base):
    """Intentos fallidos de inicio de sesión para el límite de intentos (RNF-03)."""

    __tablename__ = "failed_login_attempts"
    __table_args__ = (Index("ix_failed_login_attempts_email_attempted_at", "email", "attempted_at"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    # Sin FOREIGN KEY: el correo intentado puede no existir.
    email: Mapped[str] = mapped_column(String(254))
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordResetRequestModel(Base):
    """Solicitudes de "olvidé mi contraseña", para el límite de RNF-03 (RF-USR-08)."""

    __tablename__ = "password_reset_requests"
    __table_args__ = (Index("ix_password_reset_requests_email_requested_at", "email", "requested_at"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    # Sin FOREIGN KEY: se registra también cuando el correo no existe.
    email: Mapped[str] = mapped_column(String(254))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
