"""Adaptador HTTP del contexto de IA."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.messages import Channel, IncomingRequest
from app.shared.adapters.inbound.auth import CurrentUserId

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger("taia.ai")

# El caso de uso se compone en `app.main` (composition root) y se inyecta aqui.
# El adaptador HTTP no decide que implementacion se usa ni cuando se construye:
# construia un `GeminiLLM` por peticion y su cliente httpx nunca se cerraba.
_use_case: HandleUserMessageUseCase | None = None


def configure_ai_use_case(use_case: HandleUserMessageUseCase) -> None:
    global _use_case
    _use_case = use_case


def get_ai_use_case() -> HandleUserMessageUseCase:
    """Entrega el caso de uso ya compuesto por el composition root."""

    if _use_case is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está configurado.",
        )
    return _use_case


class AIMessageRequest(BaseModel):
    """Mensaje recibido desde un canal compatible con el asistente."""

    text: str = Field(..., min_length=1, max_length=1000)
    channel: Channel = Channel.APP


class AIMessageResponse(BaseModel):
    """Respuesta del asistente."""

    text: str
    awaiting_confirmation: bool


@router.post("/message")
def handle_message(
    payload: AIMessageRequest,
    user_id: CurrentUserId,
    use_case: Annotated[HandleUserMessageUseCase, Depends(get_ai_use_case)],
) -> AIMessageResponse:
    """Procesa un mensaje del usuario autenticado con el asistente IA."""

    reply = use_case.execute(
        IncomingRequest(
            user_id=str(user_id),
            text=payload.text,
            channel=payload.channel,
        )
    )
    # S5: el costo por intercambio se registra en el log. No se expone en la
    # respuesta porque el contrato HTTP esta congelado (ver docs/api).
    usage = use_case.last_usage()
    if usage is not None:
        logger.info(
            "ai.usage model=%s prompt=%d candidates=%d total=%d finish=%s",
            usage.model,
            usage.prompt_tokens,
            usage.candidates_tokens,
            usage.total_tokens,
            usage.finish_reason,
        )
        if usage.truncated:
            logger.warning(
                "ai.usage_truncated model=%s total=%d: la respuesta golpeo "
                "maxOutputTokens; revisar el prompt",
                usage.model,
                usage.total_tokens,
            )
    return AIMessageResponse(
        text=reply.text,
        awaiting_confirmation=reply.awaiting_confirmation,
    )
