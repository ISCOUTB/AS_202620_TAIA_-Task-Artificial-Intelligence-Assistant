import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import TEST_PASSWORD


client = TestClient(app)


@pytest.fixture(autouse=True)
def _base_de_datos_limpia(clean_db) -> None:
    """Cada prueba arranca con las tablas vacías: el repositorio ya es SQLAlchemy."""


def _register_and_login():
    register = client.post(
        "/users",
        json={"full_name": "Ana", "email": "ana@example.com", "password": TEST_PASSWORD},
    )
    assert register.status_code == 201

    login = client.post(
        "/users/login",
        json={"email": "ana@example.com", "password": TEST_PASSWORD},
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
    assert body["full_name"] == "Ana"
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
