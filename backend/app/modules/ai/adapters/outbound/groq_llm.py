"""Adaptador de salida hacia Groq, proveedor de respaldo de ADR-0011.

Unico archivo del modulo que conoce el formato de la API de Groq (compatible
con chat completions de OpenAI). Como GeminiLLM, traduce todo fallo a LLMError
y usa el mismo contrato de interpretacion."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from app.modules.ai.adapters.outbound.interpretation_contract import (
    HELP_INSTRUCTIONS,
    MAX_HELP_CHARS,
    as_data,
    interpretation_instructions,
    parse_interpretation,
)
from app.modules.ai.application.ports.llm import LLMError, LLMUsage, LLMPort
from app.modules.ai.domain.messages import IncomingRequest, Intent, Interpretation

_URL = "https://api.groq.com/openai/v1/chat/completions"
_DEFAULT_MODEL = "openai/gpt-oss-120b"
_DEFAULT_TIMEOUT = 20.0
# gpt-oss razona antes de responder y esos tokens cuentan contra
# max_completion_tokens: con poco margen, la respuesta saldria cortada.
_MAX_COMPLETION_TOKENS = 1024
# Variables de las credenciales, en el orden en que se intentan.
_KEY_VARIABLES = ("GROQ_API_KEY_1", "GROQ_API_KEY_2")


def _nullable_object(fields: tuple[str, ...]) -> dict[str, Any]:
    return {
        "type": ["object", "null"],
        "additionalProperties": False,
        "required": list(fields),
        "properties": {field: {"type": ["string", "null"]} for field in fields},
    }


# Modo estricto de Groq: todo campo va en "required" y lo opcional se expresa
# con null (https://console.groq.com/docs/structured-outputs).
_INTERPRETATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["intent", "confidence", "task", "task_hint", "filters"],
    "properties": {
        "intent": {"type": "string", "enum": [intent.value for intent in Intent]},
        "confidence": {"type": "number"},
        "task": _nullable_object(("title", "due_at", "subject", "description")),
        "task_hint": {"type": ["string", "null"]},
        "filters": _nullable_object(("text", "subject", "status", "due_from", "due_to")),
    },
}


class GroqLLM(LLMPort):
    """Implementacion de LLMPort sobre la API de Groq."""

    def __init__(
        self,
        api_key: str,
        model: str = _DEFAULT_MODEL,
        client: httpx.Client | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("falta la API key de Groq")
        self._api_key = api_key
        self._model = model
        self._client = client or httpx.Client(timeout=timeout)
        self._last_usage: LLMUsage | None = None

    @classmethod
    def all_from_env(cls) -> list["GroqLLM"]:
        """Un adaptador por cada credencial configurada, en orden.

        Sin credenciales devuelve una lista vacia: el respaldo es opcional y el
        sistema funciona solo con Gemini (ADR-0011).
        """

        model = os.getenv("GROQ_MODEL") or _DEFAULT_MODEL
        keys = [os.getenv(name, "").strip() for name in _KEY_VARIABLES]
        return [cls(api_key=key, model=model) for key in keys if key]

    def close(self) -> None:
        self._client.close()

    # -- LLMPort -----------------------------------------------------------

    def interpret(self, request: IncomingRequest, now: datetime) -> Interpretation:
        content = self._complete(
            instructions=interpretation_instructions(now),
            message=as_data("Mensaje del estudiante", request.text),
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "interpretation",
                    "strict": True,
                    "schema": _INTERPRETATION_SCHEMA,
                },
            },
        )
        return parse_interpretation(content)

    def answer_system_help(self, question: str) -> str:
        answer = self._complete(
            instructions=HELP_INSTRUCTIONS,
            message=as_data("Pregunta", question),
            temperature=0.2,
        ).strip()
        if not answer:
            raise LLMError("respuesta vacia")
        return answer[:MAX_HELP_CHARS]

    def last_usage(self) -> LLMUsage | None:
        return self._last_usage

    # -- HTTP --------------------------------------------------------------

    def _complete(
        self,
        instructions: str,
        message: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Llama a chat completions y devuelve el texto de la respuesta.

        Las reglas van como mensaje de sistema y el texto del estudiante como
        mensaje de usuario, igual que en Gemini (RF-AGT-18).
        """

        body: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": message},
            ],
            "temperature": temperature,
            "max_completion_tokens": _MAX_COMPLETION_TOKENS,
            "reasoning_effort": "low",
        }
        if response_format is not None:
            body["response_format"] = response_format
        try:
            response = self._client.post(
                _URL,
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        except httpx.HTTPError as error:
            raise LLMError(f"fallo la peticion a Groq: {type(error).__name__}") from error

        if not response.is_success:
            raise LLMError(f"Groq respondio {response.status_code}")

        try:
            data = response.json()
        except ValueError as error:
            raise LLMError("Groq devolvio un cuerpo que no es JSON") from error

        self._last_usage = _extract_usage(data, self._model)
        return _extract_text(data)


# -- capa anticorrupcion: de la respuesta de Groq a conceptos de TAIA ------


def _first_choice(data: Any) -> dict[str, Any]:
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise LLMError("Groq no devolvio opciones")
    return choices[0]


def _extract_text(data: Any) -> str:
    message = _first_choice(data).get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise LLMError("Groq no devolvio texto")
    return content


def _extract_usage(data: Any, model: str) -> LLMUsage:
    """Lee `usage` para medir el costo (S5); un campo ausente cuenta como cero."""

    def entero(valor: Any) -> int:
        return valor if isinstance(valor, int) and not isinstance(valor, bool) else 0

    usage = data.get("usage") if isinstance(data, dict) else None
    usage = usage if isinstance(usage, dict) else {}
    try:
        finish = _first_choice(data).get("finish_reason")
    except LLMError:
        finish = None
    if not isinstance(finish, str):
        finish = None
    elif finish == "length":
        # LLMUsage.truncated usa el nombre de Gemini; "length" es el de Groq.
        finish = "MAX_TOKENS"
    prompt = entero(usage.get("prompt_tokens"))
    completion = entero(usage.get("completion_tokens"))
    return LLMUsage(
        model=model,
        prompt_tokens=prompt,
        candidates_tokens=completion,
        total_tokens=entero(usage.get("total_tokens")) or prompt + completion,
        finish_reason=finish,
    )
