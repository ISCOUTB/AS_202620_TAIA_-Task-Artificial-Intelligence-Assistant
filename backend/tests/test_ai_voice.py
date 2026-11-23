"""Voz de TAIA y saludos: RF-AGT-22 y la intención `greeting` de RF-AGT-02."""

from __future__ import annotations

import ast
import inspect
import re
from datetime import datetime

import pytest

from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.application import replies
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.messages import COLOMBIA_TZ, Channel, IncomingRequest, Intent, Interpretation
from app.modules.reminders.domain.entities import reminder as reminder_entity
from app.modules.usuario.adapters.inbound import telegram_webhook

NOW = datetime(2026, 9, 10, 9, 0, tzinfo=COLOMBIA_TZ)
OCTOPUS = "\U0001F419"


def _use_case(interpretations, llm=None):
    return HandleUserMessageUseCase(
        llm=llm or FakeLLM(interpretations),
        academic=InMemoryAcademicGateway(),
        conversations=InMemoryConversationStore(),
        now=lambda: NOW,
    )


def _msg(text: str) -> IncomingRequest:
    return IncomingRequest(user_id="u1", text=text, channel=Channel.APP)


# -- RF-AGT-02: greeting ----------------------------------------------------


def test_hello_gets_taia_greeting_not_the_unknown_reply_rf_agt_02():
    llm = FakeLLM([Interpretation(Intent.GREETING, 0.95)])

    reply = _use_case(None, llm=llm).execute(_msg("Hola taia"))

    assert reply.text.startswith("¡Hola! Soy TAIA")
    assert reply.text not in replies._NOT_UNDERSTOOD
    assert reply.awaiting_confirmation is False
    # Respuesta fija: una sola llamada al modelo, la de interpretación.
    assert llm.seen == ["Hola taia"]


def test_thanks_gets_a_short_warm_reply_and_executes_nothing_rf_agt_02():
    reply = _use_case([Interpretation(Intent.GREETING, 0.9)]).execute(_msg("Gracias!"))

    assert reply.text in replies._THANKS
    assert reply.awaiting_confirmation is False


def test_goodbye_gets_a_goodbye_rf_agt_02():
    reply = _use_case([Interpretation(Intent.GREETING, 0.9)]).execute(_msg("chao, nos vemos mañana"))

    assert reply.text in replies._BYE


@pytest.mark.parametrize("text", ["ok", "Vale", "\U0001F44D", "ok \U0001F44D"])
def test_ok_or_emoji_gets_a_short_ack_rf_agt_02(text):
    reply = _use_case([Interpretation(Intent.GREETING, 0.9)]).execute(_msg(text))

    assert reply.text in replies._ACK
    assert reply.text not in replies._NOT_UNDERSTOOD


# -- RF-AGT-22: variantes ----------------------------------------------------


def test_unknown_twice_in_a_row_gets_two_different_texts_rf_agt_22():
    uc = _use_case([Interpretation(Intent.UNKNOWN, 0.9), Interpretation(Intent.UNKNOWN, 0.9)])

    first = uc.execute(_msg("canta una canción")).text
    second = uc.execute(_msg("canta otra")).text

    assert first != second
    assert {first, second} <= set(replies._NOT_UNDERSTOOD)


def test_greeting_twice_in_a_row_varies_rf_agt_22():
    uc = _use_case([Interpretation(Intent.GREETING, 0.9), Interpretation(Intent.GREETING, 0.9)])

    assert uc.execute(_msg("hola")).text != uc.execute(_msg("hola otra vez")).text


# -- RF-AGT-22: textos fijos -------------------------------------------------


def _literals(module) -> list[str]:
    tree = ast.parse(inspect.getsource(module))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
    ]


_FIXED_TEXT_SOURCES = [replies, telegram_webhook]
# Palabras que, sin tilde, delatan un texto fijo viejo (RF-AGT-22).
_UNACCENTED = re.compile(
    r"\b(entendi|examenes|periodo|titulo|encontre|marque|actualice|aplicacion|"
    r"operacion|descripcion|proxima|salon|manana|especifico)\b"
)


@pytest.mark.parametrize("module", _FIXED_TEXT_SOURCES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_fixed_texts_speak_as_taia_in_first_person_rf_agt_22(module):
    for text in _literals(module):
        assert "TAIA puede" not in text, text
        assert "el asistente" not in text.lower(), text


@pytest.mark.parametrize("module", _FIXED_TEXT_SOURCES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_fixed_texts_have_accents_rf_agt_22(module):
    for text in _literals(module):
        if " " in text:  # solo frases; no claves ni nombres de campo
            assert not _UNACCENTED.search(text.lower()), text


def test_fixed_texts_have_at_most_one_emoji_rf_agt_22():
    emoji = re.compile("[\U0001F300-\U0001FAFF]")
    texts = [
        *replies._HELLO, *replies._THANKS, *replies._BYE, *replies._ACK, *replies._NOT_UNDERSTOOD,
        telegram_webhook.LINKED_MESSAGE, telegram_webhook.NOT_LINKED_MESSAGE,
        reminder_entity.default_message("Informe", "Cálculo", NOW),
    ]
    for text in texts:
        assert len(emoji.findall(text)) <= 1, text


def test_errors_and_confirmations_have_no_emoji_rf_agt_22():
    emoji = re.compile("[\U0001F300-\U0001FAFF]")
    texts = [
        replies.service_unavailable(), replies.too_long(), replies.help_truncated(),
        telegram_webhook.LINK_INVALID_MESSAGE, telegram_webhook.TELEGRAM_TAKEN_MESSAGE,
        telegram_webhook.USER_ALREADY_LINKED_MESSAGE, telegram_webhook.INACTIVE_ACCOUNT_MESSAGE,
    ]
    for text in texts:
        assert not emoji.search(text), text


def test_default_reminder_message_has_taia_voice_rf_rec_01_rf_agt_22():
    message = reminder_entity.default_message("Informe", "Cálculo", NOW)

    assert message == f"¡Ey! Soy TAIA {OCTOPUS} Recuerda que Informe de Cálculo vence el 10/09/2026 09:00. ¡Tú puedes!"
