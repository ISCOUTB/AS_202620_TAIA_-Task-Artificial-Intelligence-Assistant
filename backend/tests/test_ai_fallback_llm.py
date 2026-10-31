"""Respaldo entre proveedores LLM (RF-AGT-20, ADR-0011)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.fallback_llm import FallbackLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.application import replies
from app.modules.ai.application.ports.llm import LLMError, LLMPort, LLMUsage
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.messages import Channel, IncomingRequest, Intent, Interpretation

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=timezone(timedelta(hours=-5)))
REQUEST = IncomingRequest(user_id="u1", text="hola", channel=Channel.APP)


class _Failing(LLMPort):
    def __init__(self) -> None:
        self.calls = 0
        self.closed = False

    def interpret(self, request, now):
        self.calls += 1
        raise LLMError("Gemini respondio 503")

    def answer_system_help(self, question):
        self.calls += 1
        raise LLMError("Gemini respondio 503")

    def close(self):
        self.closed = True


class _Answering(FakeLLM):
    def last_usage(self):
        return LLMUsage(model="respaldo", total_tokens=10)


def _answer(intent=Intent.QUERY_TASKS) -> Interpretation:
    return Interpretation(intent=intent, confidence=0.9)


def test_uses_the_first_provider_when_it_answers():
    primary, backup = _Answering([_answer()]), _Failing()

    assert FallbackLLM([primary, backup]).interpret(REQUEST, NOW).intent is Intent.QUERY_TASKS
    assert backup.calls == 0


def test_falls_back_when_the_primary_fails_rf_agt_20():
    """RF-AGT-20: Gemini falla y Groq responde -> se usa la respuesta de Groq."""
    primary, backup = _Failing(), _Answering([_answer()])
    llm = FallbackLLM([primary, backup])

    assert llm.interpret(REQUEST, NOW).intent is Intent.QUERY_TASKS
    assert primary.calls == 1
    assert llm.last_usage().model == "respaldo"


def test_tries_every_provider_in_order():
    first, second = _Failing(), _Failing()
    third = _Answering(help_answer="ayuda de respaldo")

    assert FallbackLLM([first, second, third]).answer_system_help("que haces") == "ayuda de respaldo"
    assert (first.calls, second.calls) == (1, 1)


def test_raises_llm_error_when_all_providers_fail():
    llm = FallbackLLM([_Failing(), _Failing()])

    with pytest.raises(LLMError):
        llm.interpret(REQUEST, NOW)
    assert llm.last_usage() is None


def test_use_case_fails_closed_when_all_providers_fail_rf_agt_20():
    """RF-AGT-20: fallan todos -> mensaje de servicio no disponible y nada se escribe."""
    academic = InMemoryAcademicGateway()
    use_case = HandleUserMessageUseCase(
        llm=FallbackLLM([_Failing(), _Failing()]),
        academic=academic,
        conversations=InMemoryConversationStore(),
    )

    reply = use_case.execute(REQUEST)

    assert reply.text == replies.service_unavailable()
    assert academic.list_tasks("u1", None) == []


def test_close_closes_every_provider():
    first, second = _Failing(), _Failing()

    FallbackLLM([first, second]).close()

    assert first.closed and second.closed


def test_needs_at_least_one_provider():
    with pytest.raises(ValueError):
        FallbackLLM([])
