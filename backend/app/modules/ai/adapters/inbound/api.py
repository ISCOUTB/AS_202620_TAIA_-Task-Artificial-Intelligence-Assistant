"""Adaptador HTTP del contexto de IA."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from backend.app.modules.ai.adapters.outbound.gemini_llm import GeminiLLM
from backend.app.modules.ai.adapters.outbound.in_memory_conversation_store import (
    InMemoryConversationStore,
)
from backend.app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from backend.app.modules.ai.domain.messages import Channel, IncomingRequest
from backend.app.modules.usuario.adapters.inbound.api import get_authenticated_user_id

router = APIRouter(prefix="/ai", tags=["ai"])

_conversations = InMemoryConversationStore()
_academic = AcademicGatewayAdapter()


def get_ai_use_case() -> HandleUserMessageUseCase:
    """Construye el caso de uso con los adaptadores reales de ejecución."""

    try:
        llm = GeminiLLM.from_env()
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está configurado.",
        ) from error

    return HandleUserMessageUseCase(
        llm=llm,
        academic=_academic,
        conversations=_conversations,
    )


class AIMessageRequest(BaseModel):
    """Mensaje recibido desde un canal compatible con el asistente."""

    text: str = Field(..., min_length=1, max_length=1000)
    channel: Channel = Channel.APP


class AIMessageResponse(BaseModel):
    """Respuesta del asistente."""

    text: str
    awaiting_confirmation: bool


@router.post("/message", response_model=AIMessageResponse)
def handle_message(
    payload: AIMessageRequest,
    user_id: Annotated[uuid.UUID, Depends(get_authenticated_user_id)],
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
    return AIMessageResponse(
        text=reply.text,
        awaiting_confirmation=reply.awaiting_confirmation,
    )
