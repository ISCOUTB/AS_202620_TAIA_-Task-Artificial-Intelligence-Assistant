"""Puerto de salida hacia el proveedor de lenguaje natural (hoy Gemini)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from backend.app.modules.ai.domain.messages import IncomingRequest, Interpretation


class LLMError(RuntimeError):
    """El proveedor no respondio o respondio algo inutilizable."""


class LLMPort(ABC):
    """Lo minimo que el modulo de IA necesita de un modelo de lenguaje."""

    @abstractmethod
    def interpret(self, request: IncomingRequest, now: datetime) -> Interpretation:
        """Traduce el mensaje a una intencion y datos estructurados.

        `now` es la hora local del estudiante; el proveedor la usa para
        resolver expresiones como 'manana' a una fecha concreta."""

    @abstractmethod
    def answer_system_help(self, question: str) -> str:
        """Responde una duda del estudiante sobre como funciona TAIA."""
