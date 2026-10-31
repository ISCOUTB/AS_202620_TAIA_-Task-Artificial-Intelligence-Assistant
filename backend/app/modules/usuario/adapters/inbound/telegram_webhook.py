"""Webhook del bot de Telegram (RF-TEL-02).

Telegram envía cada *update* a este endpoint con el encabezado
`X-Telegram-Bot-Api-Secret-Token`, cuyo valor se registra en `setWebhook`. Sin
ese secreto no se procesa nada. El `telegram_user_id` sale del update de
Telegram, nunca de un cuerpo armado por un cliente.
"""

from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.modules.usuario.adapters.inbound.api import ErrorResponse
from app.modules.usuario.adapters.outbound.provider import (
    repository as _repository,
    telegram_link_repository as _telegram_link_repository,
)
from app.modules.usuario.application.use_cases.link_telegram import ConfirmTelegramLinkUseCase

router = APIRouter(prefix="/telegram", tags=["telegram"])

_START_COMMAND = "/start"


class _TelegramUser(BaseModel):
    id: int


class _TelegramMessage(BaseModel):
    sender: _TelegramUser | None = Field(default=None, alias="from")
    text: str | None = None


class _TelegramUpdate(BaseModel):
    message: _TelegramMessage | None = None


@router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse, "description": "Falta el secreto del webhook o no es válido."}},
)
async def telegram_webhook(
    request: Request,
    secret_token: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> None:
    """Recibe los updates del bot y confirma la vinculación con `/start <código>`."""
    # El secreto se valida antes de leer el cuerpo: sin él la respuesta es 401
    # aunque el cuerpo no sea JSON válido.
    if not _is_valid_secret(secret_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Secreto del webhook de Telegram inválido.",
        )

    try:
        update = _TelegramUpdate.model_validate(await request.json())
    except ValueError:
        return None

    message = update.message
    if message is None or message.sender is None or message.text is None:
        return None

    command, _, code = message.text.partition(" ")
    code = code.strip()
    if command != _START_COMMAND or not code:
        # La conversación con el agente por Telegram es RF-TEL-04 (pendiente).
        return None

    try:
        await run_in_threadpool(
            ConfirmTelegramLinkUseCase(_repository, _telegram_link_repository).execute,
            code,
            message.sender.id,
        )
    except ValueError:
        # Código inválido, expirado o usado, o cuenta ya vinculada: no se vincula
        # nada. Se responde 2xx igual, porque Telegram reintenta cualquier otra
        # respuesta.
        pass


def _is_valid_secret(received: str | None) -> bool:
    expected = os.getenv("TAIA_WEBHOOK_SECRET")
    if not expected or received is None:
        return False
    return hmac.compare_digest(received.encode(), expected.encode())
