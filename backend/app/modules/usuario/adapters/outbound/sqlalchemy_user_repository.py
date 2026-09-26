"""Persistencia de Usuario en PostgreSQL (tabla `users` del diccionario de datos)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, Uuid, func, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.adapters.outbound.database import Base
from app.shared.clock import as_bogota


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("char_length(trim(full_name)) > 0", name="full_name_not_blank"),
        CheckConstraint("telegram_user_id > 0", name="telegram_user_id_positive"),
        CheckConstraint(
            "(telegram_user_id IS NULL) = (telegram_linked_at IS NULL)",
            name="telegram_link_consistent",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    telegram_linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SqlAlchemyUserRepository(UserRepository):
    """Cada operación usa su propia sesión y transacción."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, user: Usuario) -> None:
        with self._session_factory.begin() as session:
            session.add(_to_model(user))

    def save(self, user: Usuario) -> None:
        with self._session_factory.begin() as session:
            session.merge(_to_model(user))

    def get_by_id(self, user_id: uuid.UUID) -> Usuario | None:
        with self._session_factory() as session:
            model = session.get(UserModel, user_id)
            return _to_domain(model) if model is not None else None

    def get_by_email(self, email: Email) -> Usuario | None:
        return self._first(UserModel.email == email.value)

    def get_by_telegram_user_id(self, telegram_user_id: int) -> Usuario | None:
        return self._first(UserModel.telegram_user_id == telegram_user_id)

    def _first(self, condition) -> Usuario | None:
        with self._session_factory() as session:
            model = session.scalars(select(UserModel).where(condition)).first()
            return _to_domain(model) if model is not None else None


def _to_model(user: Usuario) -> UserModel:
    return UserModel(
        id=user.id,
        full_name=user.full_name,
        email=user.email.value,
        password_hash=user.password_hash,
        telegram_user_id=user.telegram_user_id,
        telegram_linked_at=user.telegram_linked_at,
        deactivated_at=user.deactivated_at,
        created_at=user.created_at,
    )


def _to_domain(model: UserModel) -> Usuario:
    return Usuario(
        id=model.id,
        full_name=model.full_name,
        email=Email(model.email),
        password_hash=model.password_hash,
        telegram_user_id=model.telegram_user_id,
        telegram_linked_at=_bogota(model.telegram_linked_at),
        deactivated_at=_bogota(model.deactivated_at),
        created_at=as_bogota(model.created_at),
    )


def _bogota(value: datetime | None) -> datetime | None:
    return as_bogota(value) if value is not None else None
