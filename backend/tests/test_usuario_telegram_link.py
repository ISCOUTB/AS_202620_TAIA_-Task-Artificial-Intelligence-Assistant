from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.modules.usuario.adapters.inbound import api

client = TestClient(app)


def _register_and_login(email: str):
    client.post("/users", json={"name": "Ana", "email": email, "password": "password123"})
    response = client.post("/users/login", json={"email": email, "password": "password123"})
    return response.json()["access_token"]


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


def test_confirm_telegram_link_links_existing_telegram_identity_and_token_is_one_time():
    email = "telegram-confirm@example.com"
    token = _register_and_login(email)
    link_response = client.post(
        "/users/me/telegram/link",
        headers={"Authorization": f"Bearer {token}"},
    )
    start_token = link_response.json()["telegram_deep_link"].split("?start=", 1)[1]

    response = client.post(
        "/users/telegram/link/confirm",
        json={"token": start_token, "telegram_user_id": 123456789},
    )

    assert response.status_code == 200
    assert response.json()["telegram_linked"] is True

    reused = client.post(
        "/users/telegram/link/confirm",
        json={"token": start_token, "telegram_user_id": 123456789},
    )
    assert reused.status_code == 400


def test_same_telegram_account_cannot_be_linked_to_two_users():
    first_token = _register_and_login("telegram-owner@example.com")
    first_link = client.post(
        "/users/me/telegram/link",
        headers={"Authorization": f"Bearer {first_token}"},
    ).json()["telegram_deep_link"].split("?start=", 1)[1]
    assert client.post(
        "/users/telegram/link/confirm",
        json={"token": first_link, "telegram_user_id": 987654321},
    ).status_code == 200

    second_token = _register_and_login("telegram-second@example.com")
    second_link = client.post(
        "/users/me/telegram/link",
        headers={"Authorization": f"Bearer {second_token}"},
    ).json()["telegram_deep_link"].split("?start=", 1)[1]

    response = client.post(
        "/users/telegram/link/confirm",
        json={"token": second_link, "telegram_user_id": 987654321},
    )
    assert response.status_code == 409
