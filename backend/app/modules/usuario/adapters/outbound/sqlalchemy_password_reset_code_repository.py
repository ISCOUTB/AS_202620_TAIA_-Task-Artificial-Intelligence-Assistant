"""Códigos de recuperación de contraseña en PostgreSQL (tabla `password_reset_tokens`, RF-USR-08)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import case, delete, select, update
from sqlalchemy.orm import sessionmaker

from app.modules.usuario.adapters.outbound.sqlalchemy_models import PasswordResetTokenModel
from app.modules.usuario.application.ports.outbound.password_reset_code_repository import (
    ActiveResetCode,
    PasswordResetCodeRepository,
)

# Retención de la tabla según el diccionario de datos (5.4).
_RETENTION = timedelta(hours=24)
_Code = PasswordResetTokenModel


class SqlAlchemyPasswordResetCodeRepository(PasswordResetCodeRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def replace(
        self, user_id: uuid.UUID, code_hash: str, created_at: datetime, expires_at: datetime
    ) -> None:
        with self._session_factory.begin() as session:
            session.execute(delete(_Code).where(_Code.created_at < created_at - _RETENTION))
            # Emitir uno nuevo invalida los anteriores: su `expires_at` pasa a la hora actual.
            session.execute(
                update(_Code)
                .where(_Code.user_id == user_id, _Code.used_at.is_(None), _Code.expires_at > created_at)
                .values(expires_at=created_at)
            )
            session.add(
                _Code(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    token_hash=code_hash,
                    created_at=created_at,
                    expires_at=expires_at,
                )
            )

    def get_active(self, user_id: uuid.UUID, now: datetime) -> ActiveResetCode | None:
        with self._session_factory() as session:
            row = session.execute(
                select(_Code.id, _Code.token_hash)
                .where(_Code.user_id == user_id, _Code.used_at.is_(None), _Code.expires_at > now)
                .order_by(_Code.created_at.desc())
                .limit(1)
            ).first()
            return ActiveResetCode(row.id, row.token_hash) if row is not None else None

    def register_failure(self, code_id: uuid.UUID, now: datetime, max_attempts: int) -> None:
        with self._session_factory.begin() as session:
            # Un solo UPDATE: dos intentos simultáneos no pierden ninguna suma.
            session.execute(
                update(_Code)
                .where(_Code.id == code_id, _Code.used_at.is_(None), _Code.expires_at > now)
                .values(
                    failed_attempts=_Code.failed_attempts + 1,
                    expires_at=case(
                        (_Code.failed_attempts + 1 >= max_attempts, now), else_=_Code.expires_at
                    ),
                )
            )

    def mark_used(self, code_id: uuid.UUID, now: datetime) -> bool:
        with self._session_factory.begin() as session:
            used = session.scalar(
                update(_Code)
                .where(_Code.id == code_id, _Code.used_at.is_(None), _Code.expires_at > now)
                .values(used_at=now)
                .returning(_Code.id)
            )
            return used is not None
