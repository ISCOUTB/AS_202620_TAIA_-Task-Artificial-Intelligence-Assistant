"""Implementacion de `AgentChat` para el canal de Telegram (RF-TEL-04, RF-AGT-01).

Usa el mismo caso de uso que la aplicacion, con el canal `telegram`, asi que las
capacidades, el contexto y el limite de uso son los mismos en los dos canales.
El usuario llega resuelto por la vinculacion de Telegram (RF-AGT-17)."""

from __future__ import annotations

from uuid import UUID

from app.modules.ai.application.ports.inbound.agent_chat import AgentReply, AgentUsageLimitError
from app.modules.ai.application.use_cases.handle_message import (
    HandleUserMessageUseCase,
    UsageLimitExceededError,
)
from app.modules.ai.domain.messages import Channel, IncomingRequest


class TelegramAgentChat:
    def __init__(self, use_case: HandleUserMessageUseCase) -> None:
        self._use_case = use_case

    def reply_telegram(self, user_id: UUID, text: str) -> AgentReply:
        try:
            reply = self._use_case.execute(
                IncomingRequest(user_id=str(user_id), text=text, channel=Channel.TELEGRAM)
            )
        except UsageLimitExceededError as error:
            # RF-AGT-19: el webhook responde el mensaje equivalente al 429.
            raise AgentUsageLimitError(str(error)) from error
        return AgentReply(text=reply.text, awaiting_confirmation=reply.awaiting_confirmation)
