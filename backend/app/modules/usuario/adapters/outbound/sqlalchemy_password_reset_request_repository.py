"""Solicitudes de recuperación de contraseña en PostgreSQL (RF-USR-08, RNF-03)."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from app.modules.usuario.adapters.outbound.sqlalchemy_models import PasswordResetRequestModel
from app.modules.usuario.application.ports.outbound.password_reset_request_repository import (
    PasswordResetRequestRepository,
)

# Retención de la tabla según el diccionario de datos (5.7).
_RETENTION = timedelta(hours=24)


class SqlAlchemyPasswordResetRequestRepository(PasswordResetRequestRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, email: str, requested_at: datetime) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                delete(PasswordResetRequestModel).where(
                    PasswordResetRequestModel.requested_at < requested_at - _RETENTION
                )
            )
            session.add(PasswordResetRequestModel(email=email, requested_at=requested_at))

    def count_since(self, email: str, since: datetime) -> int:
        with self._session_factory() as session:
            return session.scalar(
                select(func.count())
                .select_from(PasswordResetRequestModel)
                .where(
                    PasswordResetRequestModel.email == email,
                    PasswordResetRequestModel.requested_at >= since,
                )
            )
