"""Pruebas iniciales del módulo Usuario."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_register_user_returns_created_user_without_password():
    response = client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana-normalizada@example.com",
            "password": "segura123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ana"
    assert body["email"] == "ana-normalizada@example.com"
    assert body["status"] == "active"
    assert body["telegram_linked"] is False
    assert "password" not in body
    assert "password_hash" not in body


def test_register_user_rejects_duplicate_email():
    email = "duplicado@example.com"
    payload = {"name": "Uno", "email": email, "password": "segura123"}

    assert client.post("/users", json=payload).status_code == 201
    assert client.post("/users", json=payload).status_code == 409


def test_register_user_rejects_short_password():
    response = client.post(
        "/users",
        json={"name": "Ana", "email": "ana2@example.com", "password": "1234567"},
    )

    assert response.status_code == 422


def test_register_user_normalizes_email():
    response = client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "  ANA-NORMALIZADA2@Example.COM  ",
            "password": "segura123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "ana-normalizada2@example.com"


def test_login_user_returns_bearer_token_for_valid_credentials():
    email = "login@example.com"
    password = "segura123"

    register_response = client.post(
        "/users",
        json={"name": "Login", "email": email, "password": password},
    )
    assert register_response.status_code == 201

    response = client.post(
        "/users/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_user_rejects_wrong_password():
    email = "wrong-password@example.com"
    client.post(
        "/users",
        json={"name": "Login", "email": email, "password": "segura123"},
    )

    response = client.post(
        "/users/login",
        json={"email": email, "password": "incorrecta"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Correo o contraseña incorrectos."


def test_login_user_rejects_unknown_email_without_revealing_account_existence():
    response = client.post(
        "/users/login",
        json={"email": "no-existe@example.com", "password": "segura123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Correo o contraseña incorrectos."
