"""Doble de prueba del LLMPort. Devuelve respuestas preparadas de antemano;
no llama a ningun servicio. No usar fuera de las pruebas."""

from __future__ import annotations

from datetime import datetime

from app.modules.ai.application.ports.llm import LLMError, LLMPort
from app.modules.ai.domain.messages import IncomingRequest, Interpretation


class FakeLLM(LLMPort):
    def __init__(
        self,
        interpretations: list[Interpretation] | None = None,
        help_answer: str = "TAIA registra y consulta tus tareas academicas.",
    ) -> None:
        self._queue = list(interpretations or [])
        self._help_answer = help_answer
        self.seen: list[str] = []
        self.requests: list[IncomingRequest] = []

    def interpret(self, request: IncomingRequest, now: datetime) -> Interpretation:
        self.seen.append(request.text)
        self.requests.append(request)
        if not self._queue:
            raise LLMError("sin respuestas preparadas")
        return self._queue.pop(0)

    def answer_system_help(self, question: str) -> str:
        self.seen.append(question)
        return self._help_answer
