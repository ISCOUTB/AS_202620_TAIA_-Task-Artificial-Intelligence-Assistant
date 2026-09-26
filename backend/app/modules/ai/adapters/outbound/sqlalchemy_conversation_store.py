"""SQLAlchemy-backed short-term conversation storage."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from app.modules.ai.adapters.outbound.sqlalchemy_models import ConversationMessageModel, ConversationModel
from app.modules.ai.application.ports.conversation_store import ConversationStore
from app.modules.ai.domain.conversation import Conversation, Turn
from app.modules.ai.domain.messages import ActionKind, ExtractedTaskData, HISTORY_LIMIT, PendingAction

PENDING_TTL = timedelta(minutes=10)


class SqlAlchemyConversationStore(ConversationStore):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def get(self, user_id: str) -> Conversation:
        identifier = uuid.UUID(user_id)
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
            messages.reverse()
            pending = None
            now = datetime.now(timezone.utc)
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

    def save(self, conversation: Conversation) -> None:
        identifier = uuid.UUID(conversation.user_id)
        pending = _pending_to_json(conversation.pending) if conversation.pending else None
        expires_at = datetime.now(timezone.utc) + PENDING_TTL if pending else None
        with self._session_factory.begin() as session:
            state = session.get(ConversationModel, identifier)
            if state is None:
                state = ConversationModel(user_id=identifier)
                session.add(state)
            state.pending_action = pending
            state.pending_action_expires_at = expires_at
            session.flush()
            session.execute(
                delete(ConversationMessageModel).where(ConversationMessageModel.user_id == identifier)
            )
            session.add_all(
                ConversationMessageModel(user_id=identifier, role=turn.role, content=turn.text)
                for turn in conversation.turns
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
        },
        "summary": action.summary,
        "task_id": action.task_id,
        "task_hint": action.task_hint,
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
        ),
        summary=data["summary"],
        task_id=data.get("task_id"),
        task_hint=data.get("task_hint"),
    )
