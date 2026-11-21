"""Puerto de entrada de AI para conversar con el agente desde otro canal.

El webhook de Telegram (módulo Usuario) resuelve la identidad con la
vinculación y entrega aquí el texto (RF-TEL-04, RF-AGT-01). El usuario llega
resuelto por el backend, nunca por el LLM (RF-AGT-17).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class AgentReply:
    text: str
    awaiting_confirmation: bool


class AgentUsageLimitError(Exception):
    """El usuario superó el límite de mensajes al agente (RF-AGT-19)."""


class AgentChat(Protocol):
    """Contrato público de AI para el canal de Telegram."""

    def reply_telegram(self, user_id: UUID, text: str) -> AgentReply:
        """Procesa el mensaje en el canal `telegram`.

        Lanza `AgentUsageLimitError` si se supera el límite de uso.
        """
        ...


_service: AgentChat | None = None


def configure_agent_chat(service: AgentChat) -> None:
    global _service
    _service = service


def get_agent_chat() -> AgentChat:
    if _service is None:
        raise RuntimeError("El chat del agente no ha sido configurado.")
    return _service
