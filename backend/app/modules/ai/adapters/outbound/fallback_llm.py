"""Proveedor LLM con respaldo (ADR-0011).

Intenta los proveedores en orden y usa el primero que responda. Si todos
fallan, propaga LLMError y el caso de uso falla cerrado como en ADR-0007: el
caso de uso no sabe cuantos proveedores hay."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar

from app.modules.ai.application.ports.llm import LLMError, LLMUsage, LLMPort
from app.modules.ai.domain.messages import IncomingRequest, Interpretation

logger = logging.getLogger("taia.ai")

T = TypeVar("T")


class FallbackLLM(LLMPort):
    def __init__(self, providers: list[LLMPort]) -> None:
        if not providers:
            raise ValueError("se necesita al menos un proveedor")
        self._providers = providers
        self._answered: LLMPort | None = None

    def interpret(self, request: IncomingRequest, now: datetime) -> Interpretation:
        return self._first_answer(lambda provider: provider.interpret(request, now))

    def answer_system_help(self, question: str) -> str:
        return self._first_answer(lambda provider: provider.answer_system_help(question))

    def last_usage(self) -> LLMUsage | None:
        return self._answered.last_usage() if self._answered else None

    def close(self) -> None:
        for provider in self._providers:
            close = getattr(provider, "close", None)
            if close is not None:
                close()

    def _first_answer(self, call: Callable[[LLMPort], T]) -> T:
        self._answered = None
        last_error: LLMError | None = None
        for position, provider in enumerate(self._providers):
            try:
                result = call(provider)
            except LLMError as error:
                # Solo el tipo de proveedor y el motivo: nunca el mensaje (RNF-05).
                logger.warning("ai.llm_failed provider=%s reason=%s", type(provider).__name__, error)
                last_error = error
                continue
            if position > 0:
                logger.info("ai.llm_fallback provider=%s", type(provider).__name__)
            self._answered = provider
            return result
        raise LLMError("ningun proveedor LLM respondio") from last_error
