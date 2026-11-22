"""SQLAlchemy-backed short-term conversation storage."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from app.modules.ai.adapters.outbound.sqlalchemy_models import ConversationMessageModel, ConversationModel
from app.modules.ai.application.ports.conversation_store import ConversationStore
from app.modules.ai.domain.conversation import Conversation, Turn
from app.modules.ai.domain.messages import (
    CONTEXT_TTL,
    HISTORY_LIMIT,
    ActionKind,
    ExtractedTaskData,
    PendingAction,
)

# RF-AGT-04: la accion propuesta expira a los 10 minutos.
PENDING_TTL = timedelta(minutes=10)
# Retencion de conversation_messages segun el diccionario de datos (8.2).
MESSAGE_RETENTION = timedelta(hours=24)


class SqlAlchemyConversationStore(ConversationStore):
    def __init__(
        self, session_factory: sessionmaker, now: Callable[[], datetime] | None = None
    ) -> None:
        self._session_factory = session_factory
        # Reloj inyectable con zona (RT-03).
        self._now = now or (lambda: datetime.now(timezone.utc))

    def get(self, user_id: str) -> Conversation:
        """Contexto persistido (RF-AGT-15): sobrevive a reinicios y es el mismo
        para la app y Telegram. Tras 30 minutos sin mensajes, empieza vacio."""

        identifier = uuid.UUID(user_id)
        now = self._now()
        with self._session_factory() as session:
            state = session.get(ConversationModel, identifier)
            if state is None:
                return Conversation(user_id=user_id)

            messages = list(
                session.scalars(
                    select(ConversationMessageModel)
                    .where(ConversationMessageModel.user_id == identifier)
                    .order_by(ConversationMessageModel.created_at.desc(), ConversationMessageModel.id.desc())
                    .limit(HISTORY_LIMIT)
                )
            )
            if messages and messages[0].created_at <= now - CONTEXT_TTL:
                messages = []
            messages.reverse()
            pending = None
            if (
                state.pending_action is not None
                and state.pending_action_expires_at is not None
                and state.pending_action_expires_at > now
            ):
                pending = _pending_from_json(state.pending_action)
            return Conversation(
                user_id=user_id,
                turns=[Turn(role=item.role, text=item.content) for item in messages],
                pending=pending,
            )

    def take_pending(self, user_id: str) -> PendingAction | None:
        # FOR UPDATE hace esperar a una segunda peticion simultanea; al
        # continuar, PostgreSQL reevalua el WHERE sobre la fila ya vaciada y
        # no la devuelve. No se usa UPDATE ... RETURNING porque devuelve el
        # valor nuevo (NULL); el anterior solo existe desde PostgreSQL 18.
        identifier = uuid.UUID(user_id)
        with self._session_factory.begin() as session:
            state = session.scalars(
                select(ConversationModel)
                .where(
                    ConversationModel.user_id == identifier,
                    ConversationModel.pending_action.is_not(None),
                    ConversationModel.pending_action_expires_at > self._now(),
                )
                .with_for_update()
            ).first()
            if state is None:
                return None
            action = _pending_from_json(state.pending_action)
            state.pending_action = None
            state.pending_action_expires_at = None
            return action

    def save(self, conversation: Conversation) -> None:
        identifier = uuid.UUID(conversation.user_id)
        pending = _pending_to_json(conversation.pending) if conversation.pending else None
        now = self._now()
        expires_at = now + PENDING_TTL if pending else None
        with self._session_factory.begin() as session:
            state = session.get(ConversationModel, identifier)
            if state is None:
                state = ConversationModel(user_id=identifier)
                session.add(state)
            state.pending_action = pending
            state.pending_action_expires_at = expires_at
            session.flush()
            # Solo se agregan los mensajes nuevos: reescribir los anteriores les
            # cambiaria created_at y el limite de uso no podria contarlos.
            session.execute(
                delete(ConversationMessageModel).where(
                    ConversationMessageModel.user_id == identifier,
                    ConversationMessageModel.created_at < now - MESSAGE_RETENTION,
                )
            )
            session.add_all(
                ConversationMessageModel(user_id=identifier, role=turn.role, content=turn.text)
                for turn in conversation.take_unsaved()
            )

    def count_user_messages_since(self, user_id: str, since: datetime) -> int:
        with self._session_factory() as session:
            return session.scalar(
                select(func.count())
                .select_from(ConversationMessageModel)
                .where(
                    ConversationMessageModel.user_id == uuid.UUID(user_id),
                    ConversationMessageModel.role == "user",
                    ConversationMessageModel.created_at >= since,
                )
            )


def _pending_to_json(action: PendingAction) -> dict[str, Any]:
    task = action.task
    return {
        "kind": action.kind.value,
        "task": {
            "title": task.title,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "subject": task.subject,
            "description": task.description,
            "type": task.type,
            "title_generated": task.title_generated,
        },
        "summary": action.summary,
        "task_id": action.task_id,
        "task_hint": action.task_hint,
        "subject_id": action.subject_id,
    }


def _pending_from_json(data: dict[str, Any]) -> PendingAction:
    raw_task = data.get("task") or {}
    due_at = raw_task.get("due_at")
    return PendingAction(
        kind=ActionKind(data["kind"]),
        task=ExtractedTaskData(
            title=raw_task.get("title"),
            due_at=datetime.fromisoformat(due_at) if due_at else None,
            subject=raw_task.get("subject"),
            description=raw_task.get("description"),
            type=raw_task.get("type"),
            title_generated=bool(raw_task.get("title_generated")),
        ),
        summary=data["summary"],
        task_id=data.get("task_id"),
        task_hint=data.get("task_hint"),
        subject_id=data.get("subject_id"),
    )
