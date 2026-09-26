"""PostgreSQL persistence for one-time Telegram linking tokens."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.modules.usuario.adapters.outbound.sqlalchemy_models import TelegramLinkCodeModel
from app.modules.usuario.application.ports.outbound.telegram_link_repository import (
    TelegramLinkRepository,
    TelegramLinkToken,
)


class SqlAlchemyTelegramLinkRepository(TelegramLinkRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def save(self, link: TelegramLinkToken) -> None:
        with self._session_factory.begin() as session:
            session.add(
                TelegramLinkCodeModel(
                    id=uuid.uuid4(),
                    user_id=link.user_id,
                    code_hash=_hash(link.token),
                    expires_at=link.expires_at,
                    used_at=datetime.now(timezone.utc) if link.used else None,
                )
            )

    def get(self, token: str) -> TelegramLinkToken | None:
        with self._session_factory() as session:
            model = session.scalars(
                select(TelegramLinkCodeModel).where(
                    TelegramLinkCodeModel.code_hash == _hash(token)
                )
            ).first()
            if model is None:
                return None
            return TelegramLinkToken(
                token=token,
                user_id=model.user_id,
                expires_at=model.expires_at,
                used=model.used_at is not None,
            )

    def mark_used(self, token: str) -> None:
        with self._session_factory.begin() as session:
            model = session.scalars(
                select(TelegramLinkCodeModel).where(
                    TelegramLinkCodeModel.code_hash == _hash(token)
                )
            ).first()
            if model is not None and model.used_at is None:
                model.used_at = datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
