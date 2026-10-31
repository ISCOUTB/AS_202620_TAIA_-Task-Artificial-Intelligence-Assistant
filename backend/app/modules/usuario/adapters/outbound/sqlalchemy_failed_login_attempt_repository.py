"""PostgreSQL persistence for failed login attempts (RNF-03)."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from app.modules.usuario.adapters.outbound.sqlalchemy_models import FailedLoginAttemptModel
from app.modules.usuario.application.ports.outbound.failed_login_attempt_repository import (
    FailedLoginAttemptRepository,
)

# Retención de la tabla según el diccionario de datos (5.6).
_RETENTION = timedelta(hours=24)


class SqlAlchemyFailedLoginAttemptRepository(FailedLoginAttemptRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, email: str, attempted_at: datetime) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                delete(FailedLoginAttemptModel).where(
                    FailedLoginAttemptModel.attempted_at < attempted_at - _RETENTION
                )
            )
            session.add(FailedLoginAttemptModel(email=email, attempted_at=attempted_at))

    def count_since(self, email: str, since: datetime) -> int:
        with self._session_factory() as session:
            return session.scalar(
                select(func.count())
                .select_from(FailedLoginAttemptModel)
                .where(
                    FailedLoginAttemptModel.email == email,
                    FailedLoginAttemptModel.attempted_at >= since,
                )
            )
