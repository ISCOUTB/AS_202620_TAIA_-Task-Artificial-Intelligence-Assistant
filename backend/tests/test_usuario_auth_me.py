from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.modules.usuario.adapters.inbound.api import _repository


client = TestClient(app)


def setup_function() -> None:
    _repository._users.clear()


def _register_and_login():
    register = client.post(
        "/users",
        json={"name": "Ana", "email": "ana@example.com", "password": "password123"},
    )
    assert register.status_code == 201

    login = client.post(
        "/users/login",
        json={"email": "ana@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_get_me_with_valid_token_returns_user():
    token = _register_and_login()

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ana"
    assert body["email"] == "ana@example.com"
    assert body["telegram_linked"] is False
    assert "password" not in body
    assert "password_hash" not in body


def test_get_me_without_token_returns_401():
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_me_with_invalid_token_returns_401():
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
