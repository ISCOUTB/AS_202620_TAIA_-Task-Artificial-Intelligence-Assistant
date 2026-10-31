"""Límite de uso del agente (RF-AGT-19)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.main import app
from app.modules.ai.adapters.inbound.api import get_ai_use_case
from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.adapters.outbound.sqlalchemy_conversation_store import SqlAlchemyConversationStore
from app.modules.ai.adapters.outbound.sqlalchemy_models import ConversationMessageModel
from app.modules.ai.application.use_cases.handle_message import (
    HandleUserMessageUseCase,
    UsageLimitExceededError,
)
from app.modules.ai.domain.conversation import Conversation
from app.modules.ai.domain.messages import Channel, IncomingRequest, Intent, Interpretation
from tests.helpers import register_and_login


def _unknown(count: int) -> list[Interpretation]:
    return [Interpretation(intent=Intent.UNKNOWN, confidence=0.9) for _ in range(count)]


def _msg(text: str = "hola", user: str = "u1") -> IncomingRequest:
    return IncomingRequest(user_id=user, text=text, channel=Channel.APP)


def _use_case(llm, store=None, hourly=30, daily=200):
    return HandleUserMessageUseCase(
        llm=llm,
        academic=InMemoryAcademicGateway(),
        conversations=store or InMemoryConversationStore(),
        hourly_limit=hourly,
        daily_limit=daily,
    )


def test_hourly_limit_rejects_without_calling_the_llm():
    """RF-AGT-19: al superar el límite no se llama al LLM."""
    llm = FakeLLM(_unknown(3))
    use_case = _use_case(llm, hourly=2)
    use_case.execute(_msg())
    use_case.execute(_msg())

    with pytest.raises(UsageLimitExceededError):
        use_case.execute(_msg("tercero"))

    assert "tercero" not in llm.seen


def test_daily_limit_applies_independently_of_the_hourly_one():
    use_case = _use_case(FakeLLM(_unknown(3)), hourly=10, daily=2)
    use_case.execute(_msg())
    use_case.execute(_msg())

    with pytest.raises(UsageLimitExceededError):
        use_case.execute(_msg())


def test_limit_is_per_user():
    use_case = _use_case(FakeLLM(_unknown(2)), hourly=1)
    use_case.execute(_msg(user="u1"))

    assert use_case.execute(_msg(user="u2")).text


def test_rejected_messages_do_not_count():
    """Un mensaje vacío o demasiado largo no llega al LLM y no consume cupo."""
    use_case = _use_case(FakeLLM(_unknown(1)), hourly=1)
    use_case.execute(_msg("   "))
    use_case.execute(_msg("x" * 1001))

    assert use_case.execute(_msg()).text


def test_api_returns_429_when_the_limit_is_reached():
    client = TestClient(app)
    headers = register_and_login(client)
    use_case = _use_case(FakeLLM(_unknown(1)), hourly=1)
    app.dependency_overrides[get_ai_use_case] = lambda: use_case
    try:
        assert client.post("/ai/message", json={"text": "hola"}, headers=headers).status_code == 200
        response = client.post("/ai/message", json={"text": "hola"}, headers=headers)
    finally:
        app.dependency_overrides.pop(get_ai_use_case, None)

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Alcanzaste el límite de mensajes al asistente. Intenta de nuevo más tarde."
    }


def test_sqlalchemy_store_appends_messages_and_counts_only_user_ones(clean_db):
    store = SqlAlchemyConversationStore(clean_db)
    user_id = str(uuid.uuid4())
    since = datetime.now(timezone.utc) - timedelta(minutes=1)

    conversation = store.get(user_id)
    conversation.record("user", "primero")
    conversation.record("assistant", "respuesta")
    store.save(conversation)
    conversation = store.get(user_id)
    conversation.record("user", "segundo")
    conversation.record("assistant", "respuesta")
    store.save(conversation)

    assert store.count_user_messages_since(user_id, since) == 2
    assert [turn.text for turn in store.get(user_id).turns] == [
        "primero", "respuesta", "segundo", "respuesta",
    ]


def test_sqlalchemy_store_keeps_dates_and_purges_after_retention(clean_db):
    """Los mensajes guardados conservan su fecha; los de más de 24 horas se borran (diccionario 8.2)."""
    store = SqlAlchemyConversationStore(clean_db)
    user_id = str(uuid.uuid4())
    conversation = Conversation(user_id=user_id)
    conversation.record("user", "antiguo")
    store.save(conversation)
    with clean_db.begin() as session:
        session.execute(
            update(ConversationMessageModel).values(
                created_at=datetime.now(timezone.utc) - timedelta(hours=25)
            )
        )

    conversation = store.get(user_id)
    conversation.record("user", "nuevo")
    store.save(conversation)

    assert store.count_user_messages_since(user_id, datetime.now(timezone.utc) - timedelta(days=2)) == 1
    assert [turn.text for turn in store.get(user_id).turns] == ["nuevo"]
