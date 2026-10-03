"""Puerto de salida hacia el proveedor de lenguaje natural (hoy Gemini)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.modules.ai.domain.messages import IncomingRequest, Interpretation


class LLMError(RuntimeError):
    """El proveedor no respondio o respondio algo inutilizable."""


@dataclass(frozen=True)
class LLMUsage:
    """Consumo de la ultima llamada al proveedor.

    Es lo que permite medir el costo (S5). `finish_reason` distingue una
    respuesta completa de una truncada por `maxOutputTokens`, que es la
    senal de que el prompt se queda corto y hay que ajustarlo.
    """

    model: str
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str | None = None

    @property
    def truncated(self) -> bool:
        return self.finish_reason == "MAX_TOKENS"


class LLMPort(ABC):
    """Lo minimo que el modulo de IA necesita de un modelo de lenguaje."""

    def last_usage(self) -> LLMUsage | None:
        """Consumo de la ultima llamada, o None si el proveedor no lo reporta.

        No es abstracto: los dobles de prueba no tienen por que informarlo.
        """

        return None

    @abstractmethod
    def interpret(self, request: IncomingRequest, now: datetime) -> Interpretation:
        """Traduce el mensaje a una intencion y datos estructurados.

        `now` es la hora local del estudiante; el proveedor la usa para
        resolver expresiones como 'manana' a una fecha concreta."""

    @abstractmethod
    def answer_system_help(self, question: str) -> str:
        """Responde una duda del estudiante sobre como funciona TAIA."""
