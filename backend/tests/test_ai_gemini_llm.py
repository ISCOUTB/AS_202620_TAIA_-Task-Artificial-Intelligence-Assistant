"""Pruebas del adaptador de Gemini. No sale a la red: usa MockTransport."""

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.modules.ai.adapters.outbound.gemini_llm import GeminiLLM
from app.modules.ai.application.ports.llm import LLMError
from app.modules.ai.domain.messages import Channel, IncomingRequest, Intent

TZ = timezone(timedelta(hours=-5))
NOW = datetime(2026, 9, 10, 12, 0, tzinfo=TZ)
REQUEST = IncomingRequest(user_id="u1", text="crea una tarea", channel=Channel.TELEGRAM)


def _gemini(handler) -> GeminiLLM:
    return GeminiLLM(
        api_key="test-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _reply(payload) -> httpx.Response:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return httpx.Response(
        200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]}
    )


def test_interpret_translates_gemini_json():
    llm = _gemini(
        lambda request: _reply(
            {
                "intent": "create_task",
                "confidence": 0.87,
                "task": {
                    "title": "Taller de arquitectura",
                    "due_at": "2026-09-20T20:00:00-05:00",
                    "subject": "Arquitectura",
                    "description": None,
                },
                "task_hint": None,
                "filters": None,
            }
        )
    )

    result = llm.interpret(REQUEST, NOW)

    assert result.intent is Intent.CREATE_TASK
    assert result.confidence == 0.87
    assert result.task.title == "Taller de arquitectura"
    assert result.task.due_at == datetime(2026, 9, 20, 20, 0, tzinfo=TZ)
    assert result.task.description is None
    assert result.filters is None


def test_api_key_travels_in_header_not_url():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("x-goog-api-key", "")
        return _reply({"intent": "unknown", "confidence": 0.1})

    _gemini(handler).interpret(REQUEST, NOW)

    assert seen["key"] == "test-key"
    assert "test-key" not in seen["url"]


def test_prompt_includes_current_time():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen["prompt"] = body["contents"][0]["parts"][0]["text"]
        return _reply({"intent": "unknown", "confidence": 0.1})

    _gemini(handler).interpret(REQUEST, NOW)

    assert NOW.isoformat() in seen["prompt"]
    assert REQUEST.text in seen["prompt"]


def test_unknown_intent_falls_back_to_unknown():
    llm = _gemini(lambda request: _reply({"intent": "drop_database", "confidence": 0.9}))

    assert llm.interpret(REQUEST, NOW).intent is Intent.UNKNOWN


def test_confidence_is_clamped_and_sanitized():
    llm = _gemini(lambda request: _reply({"intent": "create_task", "confidence": 7.5}))
    assert llm.interpret(REQUEST, NOW).confidence == 1.0

    llm = _gemini(lambda request: _reply({"intent": "create_task", "confidence": "alta"}))
    assert llm.interpret(REQUEST, NOW).confidence == 0.0


def test_garbage_due_date_becomes_none():
    llm = _gemini(
        lambda request: _reply(
            {
                "intent": "create_task",
                "confidence": 0.9,
                "task": {"title": "Leer", "due_at": "el viernes"},
            }
        )
    )

    assert llm.interpret(REQUEST, NOW).task.due_at is None


def test_naive_due_date_gets_local_timezone():
    llm = _gemini(
        lambda request: _reply(
            {
                "intent": "create_task",
                "confidence": 0.9,
                "task": {"title": "Leer", "due_at": "2026-09-20T20:00:00"},
            }
        )
    )

    assert llm.interpret(REQUEST, NOW).task.due_at == datetime(
        2026, 9, 20, 20, 0, tzinfo=TZ
    )


def test_empty_task_fields_produce_no_task():
    llm = _gemini(
        lambda request: _reply(
            {
                "intent": "create_task",
                "confidence": 0.9,
                "task": {"title": "   ", "due_at": None},
            }
        )
    )

    assert llm.interpret(REQUEST, NOW).task is None


def test_http_error_status_raises_llm_error():
    llm = _gemini(lambda request: httpx.Response(429, json={"error": "quota"}))

    with pytest.raises(LLMError):
        llm.interpret(REQUEST, NOW)


def test_network_failure_raises_llm_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    llm = _gemini(handler)

    with pytest.raises(LLMError):
        llm.interpret(REQUEST, NOW)


def test_response_without_candidates_raises_llm_error():
    llm = _gemini(lambda request: httpx.Response(200, json={"candidates": []}))

    with pytest.raises(LLMError):
        llm.interpret(REQUEST, NOW)


def test_non_json_content_raises_llm_error():
    llm = _gemini(lambda request: _reply("esto no es json"))

    with pytest.raises(LLMError):
        llm.interpret(REQUEST, NOW)


def test_answer_system_help_returns_text():
    llm = _gemini(lambda request: _reply("TAIA registra y consulta tus tareas."))

    assert llm.answer_system_help("que puedes hacer?") == (
        "TAIA registra y consulta tus tareas."
    )


def test_answer_system_help_rejects_empty_answer():
    llm = _gemini(lambda request: _reply("   "))

    with pytest.raises(LLMError):
        llm.answer_system_help("que puedes hacer?")


def test_missing_api_key_is_rejected_at_construction():
    with pytest.raises(ValueError):
        GeminiLLM(api_key="")


def test_from_env_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        GeminiLLM.from_env()


def test_from_env_reads_key_and_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("x-goog-api-key", "")
        return _reply({"intent": "unknown", "confidence": 0.1})

    llm = GeminiLLM.from_env(client=httpx.Client(transport=httpx.MockTransport(handler)))
    llm.interpret(REQUEST, NOW)

    assert "gemini-test:generateContent" in seen["url"]
    assert seen["key"] == "k"


# -- S5: medicion del consumo por llamada -------------------------------


def test_last_usage_is_none_before_any_call():
    llm = _gemini(lambda request: _reply("hola"))

    assert llm.last_usage() is None


def test_usage_metadata_is_recorded_after_a_call():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "respuesta"}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 812,
                    "candidatesTokenCount": 96,
                    "totalTokenCount": 908,
                },
            },
        )

    llm = _gemini(handler)
    llm.answer_system_help("que puedes hacer?")

    usage = llm.last_usage()
    assert usage is not None
    assert usage.prompt_tokens == 812
    assert usage.candidates_tokens == 96
    assert usage.total_tokens == 908
    assert usage.finish_reason == "STOP"
    assert usage.truncated is False
    assert usage.model


def test_truncated_answer_is_flagged():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "respuesta"}]},
                        "finishReason": "MAX_TOKENS",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 100,
                    "candidatesTokenCount": 400,
                    "totalTokenCount": 500,
                },
            },
        )

    llm = _gemini(handler)
    llm.answer_system_help("que puedes hacer?")

    usage = llm.last_usage()
    assert usage is not None
    assert usage.truncated is True


def test_missing_usage_metadata_does_not_break_the_call():
    """Un detalle de facturacion ausente no puede tumbar la conversacion."""

    llm = _gemini(lambda request: _reply({"intent": "unknown", "confidence": 0.1}))
    result = llm.interpret(REQUEST, NOW)

    assert result.intent is Intent.UNKNOWN
    usage = llm.last_usage()
    assert usage is not None
    assert usage.total_tokens == 0
    assert usage.finish_reason is None


def test_total_tokens_is_reconstructed_when_absent():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"promptTokenCount": 30, "candidatesTokenCount": 12},
            },
        )

    llm = _gemini(handler)
    llm.answer_system_help("hola")

    usage = llm.last_usage()
    assert usage is not None
    assert usage.total_tokens == 42


def test_boolean_in_usage_metadata_is_not_counted_as_a_token():
    """`True` es un int en Python: contarlo como 1 token falsearia la medicion."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {
                    "promptTokenCount": True,
                    "candidatesTokenCount": False,
                    "totalTokenCount": 0,
                },
            },
        )

    llm = _gemini(handler)
    llm.answer_system_help("hola")

    usage = llm.last_usage()
    assert usage is not None
    assert usage.prompt_tokens == 0
    assert usage.candidates_tokens == 0
