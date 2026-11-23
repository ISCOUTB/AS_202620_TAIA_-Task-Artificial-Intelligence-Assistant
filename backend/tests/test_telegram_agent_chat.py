"""RF-TEL-04, RF-AGT-01 y RF-AGT-19: conversar con el agente desde Telegram.

El webhook responde en el mismo chat con `method: sendMessage`. El agente es un
doble de `AgentChat`, salvo en las pruebas de extremo a extremo, que usan el caso
de uso real con un LLM doble (`FakeLLM`): ninguna prueba sale a la red.
"""

from __future__ import annotations

import itertools
import logging
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.application.dto import TaskFilters
from app.modules.ai.application.ports.inbound import agent_chat
from app.modules.ai.application.ports.inbound.agent_chat import AgentReply, AgentUsageLimitError
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.application.use_cases.telegram_chat import TelegramAgentChat
from app.modules.ai.domain.messages import Channel, ExtractedTaskData, Intent, Interpretation
from app.modules.usuario.adapters.inbound.telegram_webhook import (
    INACTIVE_ACCOUNT_MESSAGE,
    NOT_LINKED_MESSAGE,
)
from app.modules.usuario.adapters.outbound.provider import repository
from app.shared.clock import now_bogota
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)
WEBHOOK_SECRET = "webhook-secret-de-prueba"
SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
LIMIT_MESSAGE = "Alcanzaste el límite de mensajes al asistente. Intenta de nuevo más tarde."
_telegram_ids = itertools.count(700_000_001)


@pytest.fixture(autouse=True)
def webhook_secret(monkeypatch):
    monkeypatch.setenv("TAIA_WEBHOOK_SECRET", WEBHOOK_SECRET)


class FakeAgentChat:
    """Doble de `AgentChat` que registra con que usuario y texto se le llamo."""

    def __init__(self, text: str = "Tienes 1 actividad(es).", limit_reached: bool = False) -> None:
        self._text = text
        self._limit_reached = limit_reached
        self.calls: list[tuple[uuid.UUID, str]] = []

    def reply_telegram(self, user_id: uuid.UUID, text: str) -> AgentReply:
        self.calls.append((user_id, text))
        if self._limit_reached:
            raise AgentUsageLimitError(LIMIT_MESSAGE)
        return AgentReply(text=self._text, awaiting_confirmation=False)


@pytest.fixture
def agent(monkeypatch):
    fake = FakeAgentChat()
    monkeypatch.setattr(agent_chat, "_service", fake)
    return fake


def _update(telegram_user_id: int, text: str, chat_id: int | None = None) -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": telegram_user_id, "is_bot": False, "first_name": "Ana"},
            "chat": {"id": chat_id or telegram_user_id, "type": "private"},
            "date": 0,
            "text": text,
        },
    }


def _send(update: dict, secret: str | None = WEBHOOK_SECRET):
    headers = {SECRET_HEADER: secret} if secret is not None else {}
    return client.post("/telegram/webhook", json=update, headers=headers)


def _linked_user() -> tuple[int, uuid.UUID]:
    """Registra un usuario y vincula una cuenta de Telegram nueva con `/start <codigo>`."""
    email = f"telegram-agent-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT})
    token = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD}).json()["access_token"]
    link = client.post("/users/me/telegram/link", headers={"Authorization": f"Bearer {token}"}).json()
    telegram_user_id = next(_telegram_ids)
    assert _send(_update(telegram_user_id, f"/start {link['telegram_deep_link'].split('?start=', 1)[1]}")).status_code == 200
    user = repository.get_by_telegram_user_id(telegram_user_id)
    assert user is not None
    return telegram_user_id, user.id


def _bot_text(response) -> str:
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "sendMessage"
    return body["text"]


# -- RF-TEL-04 --------------------------------------------------------------------


def test_linked_active_account_talks_to_the_agent_in_the_same_chat_rf_tel_04(agent):
    telegram_user_id, user_id = _linked_user()

    response = _send(_update(telegram_user_id, "que tareas tengo esta semana?"))

    assert response.status_code == 200
    assert response.json() == {
        "method": "sendMessage",
        "chat_id": telegram_user_id,
        "text": "Tienes 1 actividad(es).",
    }
    # La identidad sale de la vinculacion, no del mensaje (RF-AGT-17).
    assert agent.calls == [(user_id, "que tareas tengo esta semana?")]


def test_reply_goes_to_the_chat_of_the_update_rf_tel_04(agent):
    telegram_user_id, _ = _linked_user()

    response = _send(_update(telegram_user_id, "hola", chat_id=42))

    assert response.json()["chat_id"] == 42


def test_unlinked_account_only_gets_link_instructions_rf_tel_04(agent):
    response = _send(_update(next(_telegram_ids), "que tareas tengo?"))

    assert _bot_text(response) == NOT_LINKED_MESSAGE
    assert agent.calls == []


def test_inactive_account_gets_the_fixed_message_and_no_data_rf_tel_04(agent):
    telegram_user_id, user_id = _linked_user()
    user = repository.get_by_id(user_id)
    user.deactivated_at = now_bogota()
    repository.save(user)

    response = _send(_update(telegram_user_id, "que tareas tengo?"))

    assert _bot_text(response) == INACTIVE_ACCOUNT_MESSAGE == "Lo siento, por ahora no puedo ayudarte con esta cuenta."
    assert agent.calls == []


@pytest.mark.parametrize("secret", [None, "secreto-incorrecto"])
def test_secret_is_checked_before_talking_to_the_agent_rf_tel_02(agent, secret):
    telegram_user_id, _ = _linked_user()

    response = _send(_update(telegram_user_id, "que tareas tengo?"), secret=secret)

    assert response.status_code == 401
    assert agent.calls == []


@pytest.mark.parametrize(
    "message",
    [
        {"from": {"id": 1}, "chat": {"id": 1}},
        {"chat": {"id": 1}, "text": "hola"},
        {"from": {"id": 1}, "text": "hola"},
    ],
)
def test_updates_without_text_sender_or_chat_get_no_reply_rf_tel_04(agent, message):
    response = _send({"update_id": 1, "message": message})

    assert response.status_code == 204
    assert agent.calls == []


def test_user_text_is_not_written_to_the_log_rnf_05(agent, caplog):
    telegram_user_id, _ = _linked_user()
    secret_text = "mi texto privado de prueba 8f3a"

    with caplog.at_level(logging.DEBUG):
        _send(_update(telegram_user_id, secret_text))

    assert agent.calls
    assert all(secret_text not in record.getMessage() for record in caplog.records)


# -- RF-AGT-19 --------------------------------------------------------------------


def test_usage_limit_gets_the_equivalent_of_429_rf_agt_19(monkeypatch):
    fake = FakeAgentChat(limit_reached=True)
    monkeypatch.setattr(agent_chat, "_service", fake)
    telegram_user_id, _ = _linked_user()

    response = _send(_update(telegram_user_id, "hola"))

    assert _bot_text(response) == LIMIT_MESSAGE


class _NeverCalledLLM(FakeLLM):
    def interpret(self, request, now):
        raise AssertionError("con el limite superado no se llama al LLM")


def test_usage_limit_from_telegram_does_not_call_the_llm_rf_agt_19():
    store = InMemoryConversationStore()
    use_case = HandleUserMessageUseCase(
        llm=_NeverCalledLLM(), academic=InMemoryAcademicGateway(), conversations=store, hourly_limit=0
    )

    with pytest.raises(AgentUsageLimitError, match="límite de mensajes"):
        TelegramAgentChat(use_case).reply_telegram(uuid.uuid4(), "hola")


# -- RF-AGT-01: mismas capacidades en los dos canales ---------------------------------


class _ChannelSpyLLM(FakeLLM):
    def __init__(self, interpretations) -> None:
        super().__init__(interpretations)
        self.channels: list[Channel] = []

    def interpret(self, request, now):
        self.channels.append(request.channel)
        return super().interpret(request, now)


def test_telegram_agent_uses_the_telegram_channel_rf_agt_01():
    llm = _ChannelSpyLLM([Interpretation(Intent.UNKNOWN, 0.9)])
    use_case = HandleUserMessageUseCase(
        llm=llm, academic=InMemoryAcademicGateway(), conversations=InMemoryConversationStore()
    )

    reply = TelegramAgentChat(use_case).reply_telegram(uuid.uuid4(), "hola")

    assert llm.channels == [Channel.TELEGRAM]
    assert reply.awaiting_confirmation is False


def test_main_configures_the_telegram_agent_on_the_shared_use_case_rf_agt_01():
    assert isinstance(agent_chat.get_agent_chat(), TelegramAgentChat)


def test_create_and_confirm_a_task_from_telegram_rf_agt_01(monkeypatch):
    """De extremo a extremo por el webhook: propuesta, confirmacion con "si" y creacion."""
    telegram_user_id, user_id = _linked_user()
    academic = InMemoryAcademicGateway()
    academic.add_subject(str(user_id), "Física")
    due = datetime(2026, 12, 4, 23, 59, tzinfo=timezone(timedelta(hours=-5)))
    llm = FakeLLM([
        Interpretation(Intent.CREATE_TASK, 0.9, task=ExtractedTaskData(title="Informe", due_at=due, subject="fisica"))
    ])
    use_case = HandleUserMessageUseCase(llm=llm, academic=academic, conversations=InMemoryConversationStore())
    monkeypatch.setattr(agent_chat, "_service", TelegramAgentChat(use_case))

    proposal = _bot_text(_send(_update(telegram_user_id, "crea el informe de fisica para el 4 de diciembre")))
    done = _bot_text(_send(_update(telegram_user_id, "si")))

    assert proposal.endswith("¿Lo confirmo? (sí / no)")
    assert done.startswith('¡Listo! Ya creé la tarea "Informe"')
    assert [task.title for task in academic.list_tasks(str(user_id), TaskFilters())] == ["Informe"]
