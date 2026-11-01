"""Persistencia de sesiones y tokens de renovación en PostgreSQL (RF-USR-03, 04)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from app.modules.usuario.adapters.outbound.sqlalchemy_models import RefreshTokenModel, SessionModel
from app.modules.usuario.application.ports.outbound.session_repository import (
    RefreshTokenRecord,
    SessionRepository,
)


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(
        self, session_id: uuid.UUID, user_id: uuid.UUID, refresh_token: str, expires_at: datetime
    ) -> None:
        with self._session_factory.begin() as session:
            session.add(SessionModel(id=session_id, user_id=user_id))
            # Sin relationship() el orden de inserción no está garantizado.
            session.flush()
            session.add(_refresh_token_model(session_id, refresh_token, expires_at))

    def is_active(self, session_id: uuid.UUID) -> bool:
        with self._session_factory() as session:
            found = session.scalar(
                select(SessionModel.id).where(
                    SessionModel.id == session_id, SessionModel.revoked_at.is_(None)
                )
            )
            return found is not None

    def get_refresh_token(self, refresh_token: str) -> RefreshTokenRecord | None:
        with self._session_factory() as session:
            row = session.execute(
                select(RefreshTokenModel, SessionModel)
                .join(SessionModel, SessionModel.id == RefreshTokenModel.session_id)
                .where(RefreshTokenModel.token_hash == _hash(refresh_token))
            ).first()
            if row is None:
                return None
            token, owner = row
            return RefreshTokenRecord(
                session_id=owner.id,
                user_id=owner.user_id,
                expires_at=token.expires_at,
                used=token.used_at is not None,
                session_revoked=owner.revoked_at is not None,
            )

    def rotate_refresh_token(
        self, old_token: str, new_token: str, expires_at: datetime, used_at: datetime
    ) -> bool:
        with self._session_factory.begin() as session:
            # El UPDATE condicional evita que dos renovaciones simultáneas usen el mismo token.
            session_id = session.scalar(
                update(RefreshTokenModel)
                .where(
                    RefreshTokenModel.token_hash == _hash(old_token),
                    RefreshTokenModel.used_at.is_(None),
                )
                .values(used_at=used_at)
                .returning(RefreshTokenModel.session_id)
            )
            if session_id is None:
                return False
            session.add(_refresh_token_model(session_id, new_token, expires_at))
            return True

    def revoke(self, session_id: uuid.UUID, revoked_at: datetime) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                update(SessionModel)
                .where(SessionModel.id == session_id, SessionModel.revoked_at.is_(None))
                .values(revoked_at=revoked_at, fcm_token=None)
            )

    def revoke_all(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                update(SessionModel)
                .where(SessionModel.user_id == user_id, SessionModel.revoked_at.is_(None))
                .values(revoked_at=revoked_at, fcm_token=None)
            )


def _refresh_token_model(session_id: uuid.UUID, refresh_token: str, expires_at: datetime) -> RefreshTokenModel:
    return RefreshTokenModel(
        id=uuid.uuid4(),
        session_id=session_id,
        token_hash=_hash(refresh_token),
        expires_at=expires_at,
    )


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
