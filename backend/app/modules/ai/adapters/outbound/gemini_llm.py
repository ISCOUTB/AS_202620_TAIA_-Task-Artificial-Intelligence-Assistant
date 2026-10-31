"""Adaptador de salida hacia Gemini; implementa LLMPort con httpx.

Unico archivo del modulo que conoce el formato de la API de Gemini. Su segunda
responsabilidad es la capa anticorrupcion: traducir la respuesta cruda a los
conceptos de TAIA, sin dejar pasar nada malformado."""

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

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
# gemini-2.5-flash dejo de estar accesible para proyectos nuevos: la pagina de
# deprecaciones de Google limito su acceso a las cuentas que ya lo usaban. Con
# este valor por defecto, un clon sin GEMINI_MODEL recibia 404. Ver
# docs/arc42/11-riesgos-y-deudas-tecnicas.md, seccion 11.7.
_DEFAULT_MODEL = "gemini-3.5-flash-lite"
_DEFAULT_TIMEOUT = 20.0


_INTERPRETATION_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "enum": [intent.value for intent in Intent],
        },
        "confidence": {"type": "NUMBER"},
        "task": {
            "type": "OBJECT",
            "nullable": True,
            "properties": {
                "title": {"type": "STRING", "nullable": True},
                "due_at": {"type": "STRING", "nullable": True},
                "subject": {"type": "STRING", "nullable": True},
                "description": {"type": "STRING", "nullable": True},
            },
        },
        "task_hint": {"type": "STRING", "nullable": True},
        "filters": {
            "type": "OBJECT",
            "nullable": True,
            "properties": {
                "text": {"type": "STRING", "nullable": True},
                "subject": {"type": "STRING", "nullable": True},
                "status": {"type": "STRING", "nullable": True},
                "due_from": {"type": "STRING", "nullable": True},
                "due_to": {"type": "STRING", "nullable": True},
            },
        },
    },
    "required": ["intent", "confidence"],
}


class GeminiLLM(LLMPort):
    """Implementacion de LLMPort sobre la API REST de Gemini."""

    def __init__(
        self,
        api_key: str,
        model: str = _DEFAULT_MODEL,
        client: httpx.Client | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("falta la API key de Gemini")
        self._api_key = api_key
        self._model = model
        self._client = client or httpx.Client(timeout=timeout)
        self._last_usage: LLMUsage | None = None

    @classmethod
    def from_env(cls, client: httpx.Client | None = None) -> "GeminiLLM":
        """Construye el adaptador leyendo GEMINI_API_KEY y GEMINI_MODEL."""

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no esta configurada")
        return cls(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL") or _DEFAULT_MODEL,
            client=client,
        )

    def close(self) -> None:
        self._client.close()

    # -- LLMPort -----------------------------------------------------------

    def interpret(self, request: IncomingRequest, now: datetime) -> Interpretation:
        payload = self._generate(
            instructions=interpretation_instructions(now),
            message=as_data("Mensaje del estudiante", request.text),
            config={
                "responseMimeType": "application/json",
                "responseSchema": _INTERPRETATION_SCHEMA,
                "temperature": 0,
                "maxOutputTokens": 512,
            },
        )
        return parse_interpretation(payload)

    def answer_system_help(self, question: str) -> str:
        text = self._generate(
            instructions=HELP_INSTRUCTIONS,
            message=as_data("Pregunta", question),
            config={"temperature": 0.2, "maxOutputTokens": 400},
        )
        answer = text.strip()
        if not answer:
            raise LLMError("respuesta vacia")
        return answer[:MAX_HELP_CHARS]

    # -- HTTP --------------------------------------------------------------

    def _generate(self, instructions: str, message: str, config: dict[str, Any]) -> str:
        """Llama a generateContent y devuelve el texto de la respuesta.

        RF-AGT-18: las reglas van en systemInstruction y el texto del estudiante
        en el contenido del usuario, de modo que el mensaje nunca se mezcla con
        las instrucciones en un mismo texto.
        """

        body = {
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [{"text": message}]}],
            "generationConfig": config,
        }
        try:
            response = self._client.post(
                f"{_BASE_URL}/{self._model}:generateContent",
                json=body,
                # La key va en cabecera, no en la URL, para no filtrarla en logs.
                headers={"x-goog-api-key": self._api_key},
            )
        except httpx.HTTPError as error:
            raise LLMError(f"fallo la peticion a Gemini: {type(error).__name__}") from error

        if not response.is_success:
            raise LLMError(f"Gemini respondio {response.status_code}")

        try:
            data = response.json()
        except ValueError as error:
            raise LLMError("Gemini devolvio un cuerpo que no es JSON") from error

        self._last_usage = _extract_usage(data, self._model)
        return _extract_text(data)

    def last_usage(self) -> LLMUsage | None:
        return self._last_usage


# -- capa anticorrupcion: de la respuesta de Gemini a conceptos de TAIA ----


def _extract_text(data: Any) -> str:
    """Saca el texto del primer candidato; falla si la forma no es la esperada."""

    if not isinstance(data, dict):
        raise LLMError("respuesta de Gemini con forma inesperada")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise LLMError("Gemini no devolvio candidatos")
    parts = (candidates[0] or {}).get("content", {}).get("parts")
    if not isinstance(parts, list) or not parts:
        raise LLMError("Gemini no devolvio contenido")
    text = (parts[0] or {}).get("text")
    if not isinstance(text, str):
        raise LLMError("Gemini no devolvio texto")
    return text


def _extract_usage(data: Any, model: str) -> LLMUsage:
    """Lee `usageMetadata` para poder medir el costo por llamada (S5).

    Gemini no garantiza todos los campos, y con cortes de precio se creo
    `thoughtsTokenCount`, asi que cualquier campo ausente se trata como cero en
    lugar de fallar: un detalle de facturacion no debe tumbar la conversacion.
    """

    def entero(valor: Any) -> int:
        return valor if isinstance(valor, int) and not isinstance(valor, bool) else 0

    bruto = data.get("usageMetadata") if isinstance(data, dict) else None
    bruto = bruto if isinstance(bruto, dict) else {}

    candidates = data.get("candidates") if isinstance(data, dict) else None
    finish: str | None = None
    if isinstance(candidates, list) and candidates and isinstance(candidates[0], dict):
        bruto_finish = candidates[0].get("finishReason")
        if isinstance(bruto_finish, str):
            finish = bruto_finish

    total = entero(bruto.get("totalTokenCount"))
    prompt = entero(bruto.get("promptTokenCount"))
    candidatos_tok = entero(bruto.get("candidatesTokenCount"))
    if total == 0:
        total = prompt + candidatos_tok

    return LLMUsage(
        model=model,
        prompt_tokens=prompt,
        candidates_tokens=candidatos_tok,
        total_tokens=total,
        finish_reason=finish,
    )
