"""Pruebas del adaptador de Groq (ADR-0011). No sale a la red: usa MockTransport."""

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.modules.ai.adapters.outbound.groq_llm import GroqLLM
from app.modules.ai.application.ports.llm import LLMError
from app.modules.ai.domain.messages import Channel, IncomingRequest, Intent

TZ = timezone(timedelta(hours=-5))
NOW = datetime(2026, 10, 30, 12, 0, tzinfo=TZ)
REQUEST = IncomingRequest(user_id="u1", text="crea una tarea", channel=Channel.APP)


def _groq(handler) -> GroqLLM:
    return GroqLLM(api_key="test-key", client=httpx.Client(transport=httpx.MockTransport(handler)))


def _reply(content, finish="stop", usage=None) -> httpx.Response:
    text = content if isinstance(content, str) else json.dumps(content)
    body = {"choices": [{"message": {"content": text}, "finish_reason": finish}]}
    if usage is not None:
        body["usage"] = usage
    return httpx.Response(200, json=body)


def test_interpret_translates_the_json_answer():
    llm = _groq(lambda request: _reply({
        "intent": "create_task",
        "confidence": 0.9,
        "task": {"title": "Informe", "due_at": "2026-11-02T20:00:00-05:00", "subject": "Redes", "description": None},
        "task_hint": None,
        "filters": None,
    }))

    result = llm.interpret(REQUEST, NOW)

    assert result.intent is Intent.CREATE_TASK
    assert result.task.title == "Informe"
    assert result.task.due_at == datetime(2026, 11, 2, 20, 0, tzinfo=TZ)


def test_request_uses_bearer_strict_schema_and_separates_the_student_text_rf_agt_18():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return _reply({"intent": "unknown", "confidence": 0.1, "task": None, "task_hint": None, "filters": None})

    _groq(handler).interpret(REQUEST, NOW)

    body = seen["body"]
    assert seen["auth"] == "Bearer test-key"
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["response_format"]["json_schema"]["strict"] is True
    system, user = body["messages"]
    assert system["role"] == "system"
    # El dia de la semana evita que "el lunes" se resuelva mal (2026-10-30 es viernes).
    assert f"viernes {NOW.isoformat()}" in system["content"]
    assert REQUEST.text not in system["content"]
    assert user == {"role": "user", "content": f"Mensaje del estudiante, entre marcas:\n<<<\n{REQUEST.text}\n>>>"}


def test_unknown_intent_falls_back_to_unknown():
    llm = _groq(lambda request: _reply({"intent": "delete_everything", "confidence": 0.9}))

    assert llm.interpret(REQUEST, NOW).intent is Intent.UNKNOWN


@pytest.mark.parametrize("status", [400, 401, 429, 500, 503])
def test_error_status_raises_llm_error(status):
    llm = _groq(lambda request: httpx.Response(status, json={"error": {"message": "x"}}))

    with pytest.raises(LLMError):
        llm.interpret(REQUEST, NOW)


def test_network_failure_raises_llm_error():
    def handler(request):
        raise httpx.ConnectTimeout("sin red")

    with pytest.raises(LLMError):
        _groq(handler).interpret(REQUEST, NOW)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="no es json"),
        httpx.Response(200, json={"choices": []}),
        httpx.Response(200, json={"choices": [{"message": {"content": None}}]}),
        _reply("esto no es el JSON pedido"),
    ],
)
def test_malformed_answers_raise_llm_error(response):
    with pytest.raises(LLMError):
        _groq(lambda request: response).interpret(REQUEST, NOW)


def test_usage_is_recorded_and_length_counts_as_truncated():
    llm = _groq(lambda request: _reply(
        {"intent": "unknown", "confidence": 0.1},
        finish="length",
        usage={"prompt_tokens": 600, "completion_tokens": 1024, "total_tokens": 1624},
    ))

    llm.interpret(REQUEST, NOW)
    usage = llm.last_usage()

    assert (usage.prompt_tokens, usage.candidates_tokens, usage.total_tokens) == (600, 1024, 1624)
    assert usage.truncated is True


def test_answer_system_help_returns_text_and_rejects_empty():
    assert _groq(lambda request: _reply("  TAIA registra tareas.  ")).answer_system_help("que haces") == "TAIA registra tareas."
    with pytest.raises(LLMError):
        _groq(lambda request: _reply("   ")).answer_system_help("que haces")


def test_all_from_env_builds_one_adapter_per_configured_key_in_order(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY_1", "clave-1")
    monkeypatch.setenv("GROQ_API_KEY_2", "clave-2")
    monkeypatch.setenv("GROQ_MODEL", "otro/modelo")

    adapters = GroqLLM.all_from_env()

    assert [adapter._api_key for adapter in adapters] == ["clave-1", "clave-2"]
    assert all(adapter._model == "otro/modelo" for adapter in adapters)


def test_all_from_env_skips_empty_keys(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY_1", "")
    monkeypatch.setenv("GROQ_API_KEY_2", "clave-2")

    assert [adapter._api_key for adapter in GroqLLM.all_from_env()] == ["clave-2"]

    monkeypatch.setenv("GROQ_API_KEY_2", "  ")
    assert GroqLLM.all_from_env() == []
