"""Webhook del bot de Telegram (RF-TEL-02 y RF-TEL-04).

Telegram envía cada *update* a este endpoint con el encabezado
`X-Telegram-Bot-Api-Secret-Token`, cuyo valor se registra en `setWebhook`. Sin
ese secreto no se procesa nada. El `telegram_user_id` sale del update de
Telegram, nunca de un cuerpo armado por un cliente.

`/start <código>` confirma la vinculación. Cualquier otro mensaje se conversa con
el agente (RF-TEL-04). La respuesta va en el cuerpo del webhook con
`method: sendMessage`, que Telegram ejecuta en el mismo chat: así este módulo no
necesita un cliente HTTP de Telegram. El texto del usuario no se registra en el
log (RNF-05).
"""

from __future__ import annotations

import hmac
import os
from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.modules.ai.application.ports.inbound.agent_chat import AgentUsageLimitError, get_agent_chat
from app.modules.usuario.adapters.inbound.api import ErrorResponse
from app.modules.usuario.adapters.outbound.provider import (
    repository as _repository,
    telegram_link_repository as _telegram_link_repository,
)
from app.modules.usuario.application.use_cases.link_telegram import (
    ConfirmTelegramLinkUseCase,
    TelegramAlreadyLinkedError,
    UserAlreadyLinkedError,
)
from app.modules.usuario.domain.entities.usuario import UserStatus

router = APIRouter(prefix="/telegram", tags=["telegram"])

_START_COMMAND = "/start"

_OCTOPUS = "\U0001F419"

# RF-TEL-04: una cuenta de Telegram sin vincular solo recibe cómo vincularla (RF-TEL-01).
NOT_LINKED_MESSAGE = (
    "¡Hola! Soy TAIA, tu compañera de estudio. Para ayudarte desde Telegram necesito que "
    "vinculemos tu cuenta: en la app pide el enlace de Telegram, ábrelo y pulsa Iniciar. "
    "Vale 10 minutos."
)
# RF-TEL-04: una cuenta TAIA inactiva no recibe información de la cuenta.
INACTIVE_ACCOUNT_MESSAGE = "Lo siento, por ahora no puedo ayudarte con esta cuenta."

# RF-TEL-01: el resultado de la vinculación se cuenta en el chat, con la voz de TAIA (RF-AGT-22).
LINKED_MESSAGE = (
    f"¡Listo, tu Telegram ya quedó vinculado! {_OCTOPUS} Desde aquí puedes pedirme que cree, "
    "consulte o complete tus tareas."
)
LINK_INVALID_MESSAGE = (
    "Ese enlace ya no sirve: dura 10 minutos y solo se usa una vez. Pide uno nuevo en la "
    "app y lo intentamos otra vez."
)
TELEGRAM_TAKEN_MESSAGE = (
    "Esta cuenta de Telegram ya está vinculada a otra cuenta de TAIA. Desvincúlala desde "
    "esa cuenta en la app y vuelve a intentarlo."
)
USER_ALREADY_LINKED_MESSAGE = (
    "Tu cuenta de TAIA ya tiene otro Telegram vinculado. Desvincúlalo en la app y pide un "
    "enlace nuevo."
)


class _TelegramUser(BaseModel):
    id: int


class _TelegramChat(BaseModel):
    id: int


class _TelegramMessage(BaseModel):
    sender: _TelegramUser | None = Field(default=None, alias="from")
    chat: _TelegramChat | None = None
    text: str | None = None


class _TelegramUpdate(BaseModel):
    message: _TelegramMessage | None = None


class TelegramSendMessage(BaseModel):
    """Respuesta que Telegram ejecuta como `sendMessage` en el chat del update (RF-TEL-04)."""

    method: Literal["sendMessage"] = "sendMessage"
    chat_id: int
    text: str


@router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        200: {"model": TelegramSendMessage, "description": "Respuesta del bot en el mismo chat (RF-TEL-01, RF-TEL-04)."},
        401: {"model": ErrorResponse, "description": "Falta el secreto del webhook o no es válido."},
    },
)
async def telegram_webhook(
    request: Request,
    secret_token: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> Response:
    """Recibe los updates del bot: vincula con `/start <código>` y conversa con el agente."""
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
        return _no_reply()

    message = update.message
    if message is None or message.sender is None or message.text is None:
        return _no_reply()

    command, _, code = message.text.partition(" ")
    code = code.strip()
    if command != _START_COMMAND or not code:
        if message.chat is None:
            return _no_reply()
        answer = await run_in_threadpool(_converse, message.sender.id, message.text)
        return JSONResponse(TelegramSendMessage(chat_id=message.chat.id, text=answer).model_dump())

    try:
        await run_in_threadpool(
            ConfirmTelegramLinkUseCase(_repository, _telegram_link_repository).execute,
            code,
            message.sender.id,
        )
        answer = LINKED_MESSAGE
    except TelegramAlreadyLinkedError:
        answer = TELEGRAM_TAKEN_MESSAGE
    except UserAlreadyLinkedError:
        answer = USER_ALREADY_LINKED_MESSAGE
    except ValueError:
        # Código inválido, expirado o usado. Se responde 2xx igual, porque
        # Telegram reintenta cualquier otra respuesta (RF-TEL-01, RF-TEL-02).
        answer = LINK_INVALID_MESSAGE
    if message.chat is None:
        return _no_reply()
    return JSONResponse(TelegramSendMessage(chat_id=message.chat.id, text=answer).model_dump())


def _converse(telegram_user_id: int, text: str) -> str:
    """Resuelve la identidad por la vinculación y conversa con el agente (RF-TEL-04)."""

    user = _repository.get_by_telegram_user_id(telegram_user_id)
    if user is None:
        return NOT_LINKED_MESSAGE
    if user.status is UserStatus.INACTIVE:
        return INACTIVE_ACCOUNT_MESSAGE
    try:
        return get_agent_chat().reply_telegram(user.id, text).text
    except AgentUsageLimitError as error:
        # RF-AGT-19: el mismo mensaje del 429 de la aplicación, sin llamar al LLM.
        return str(error)


def _no_reply() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _is_valid_secret(received: str | None) -> bool:
    expected = os.getenv("TAIA_WEBHOOK_SECRET")
    if not expected or received is None:
        return False
    return hmac.compare_digest(received.encode(), expected.encode())
