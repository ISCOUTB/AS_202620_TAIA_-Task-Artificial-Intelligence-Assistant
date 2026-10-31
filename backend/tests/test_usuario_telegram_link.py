import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.provider import repository
from tests.helpers import TEST_PASSWORD

client = TestClient(app)

WEBHOOK_SECRET = "webhook-secret-de-prueba"
SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


@pytest.fixture(autouse=True)
def webhook_secret(monkeypatch):
    monkeypatch.setenv("TAIA_WEBHOOK_SECRET", WEBHOOK_SECRET)


def _register_and_login(email: str):
    client.post("/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD})
    response = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})
    return response.json()["access_token"]


def _link_code(access_token: str) -> str:
    response = client.post(
        "/users/me/telegram/link",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()["telegram_deep_link"].split("?start=", 1)[1]


def _update(telegram_user_id: int, text: str) -> dict:
    """Update de Telegram como el que envía el bot al pulsar Iniciar."""
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": telegram_user_id, "is_bot": False, "first_name": "Ana"},
            "chat": {"id": telegram_user_id, "type": "private"},
            "date": 0,
            "text": text,
        },
    }


def _send(update: dict, secret: str | None = WEBHOOK_SECRET):
    headers = {SECRET_HEADER: secret} if secret is not None else {}
    return client.post("/telegram/webhook", json=update, headers=headers)


def _telegram_linked(access_token: str) -> bool:
    response = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    return response.json()["telegram_linked"]


def test_generate_telegram_link_requires_auth_and_returns_deep_link():
    email = "telegram-link@example.com"
    token = _register_and_login(email)

    response = client.post(
        "/users/me/telegram/link",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["telegram_deep_link"].startswith("https://t.me/taia_bot?start=")
    assert body["expires_at"]


def test_webhook_start_command_links_the_telegram_sender():
    """RF-TEL-01, RF-TEL-02: el telegram_user_id sale del update del bot."""
    token = _register_and_login("telegram-confirm@example.com")
    code = _link_code(token)

    response = _send(_update(123456789, f"/start {code}"))

    assert response.status_code == 204
    assert _telegram_linked(token) is True
    assert repository.get_by_telegram_user_id(123456789) is not None


@pytest.mark.parametrize("secret", [None, "secreto-incorrecto"])
def test_webhook_without_correct_secret_returns_401_and_links_nothing(secret):
    """RF-TEL-02: sin el secreto correcto -> 401 y no se vincula nada."""
    token = _register_and_login(f"telegram-no-secret-{secret}@example.com")
    code = _link_code(token)

    response = _send(_update(111111111, f"/start {code}"), secret=secret)

    assert response.status_code == 401
    assert response.json() == {"detail": "Secreto del webhook de Telegram inválido."}
    assert _telegram_linked(token) is False


def test_webhook_rejects_everything_when_secret_is_not_configured(monkeypatch):
    """RF-TEL-02: sin TAIA_WEBHOOK_SECRET ninguna petición tiene el secreto correcto."""
    monkeypatch.delenv("TAIA_WEBHOOK_SECRET")
    token = _register_and_login("telegram-unconfigured@example.com")
    code = _link_code(token)

    response = _send(_update(222222222, f"/start {code}"), secret="")

    assert response.status_code == 401
    assert _telegram_linked(token) is False


def test_webhook_checks_secret_before_reading_the_body():
    """RF-TEL-02: un cuerpo que no es JSON sin secreto también es 401."""
    response = client.post("/telegram/webhook", content=b"no es json")

    assert response.status_code == 401


def test_link_code_is_one_time():
    """RF-TEL-01: usar el mismo código dos veces -> la segunda vez falla."""
    token = _register_and_login("telegram-one-time@example.com")
    code = _link_code(token)
    assert _send(_update(333333333, f"/start {code}")).status_code == 204

    reused = _send(_update(444444444, f"/start {code}"))

    # Telegram reintenta cualquier respuesta que no sea 2xx: el rechazo no cambia el código.
    assert reused.status_code == 204
    assert repository.get_by_telegram_user_id(444444444) is None


def test_same_telegram_account_cannot_be_linked_to_two_users():
    """RF-TEL-01: una cuenta de Telegram solo se vincula a una cuenta TAIA."""
    first_token = _register_and_login("telegram-owner@example.com")
    assert _send(_update(987654321, f"/start {_link_code(first_token)}")).status_code == 204

    second_token = _register_and_login("telegram-second@example.com")
    response = _send(_update(987654321, f"/start {_link_code(second_token)}"))

    assert response.status_code == 204
    assert _telegram_linked(second_token) is False


@pytest.mark.parametrize("text", ["hola", "/start", "/ayuda codigo"])
def test_webhook_ignores_messages_that_are_not_a_start_code(text):
    response = _send(_update(555555555, text))

    assert response.status_code == 204
    assert repository.get_by_telegram_user_id(555555555) is None


def test_webhook_ignores_updates_without_message():
    response = _send({"update_id": 2, "edited_message": {"text": "hola"}})

    assert response.status_code == 204
