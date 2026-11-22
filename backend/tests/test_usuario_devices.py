"""Token FCM de la sesión y puerto `UserDeviceDirectory` (RF-NOT-01, RF-USR-04, RF-USR-09)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.modules.usuario.adapters.outbound.in_memory_session_repository import InMemorySessionRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.application.ports.inbound.user_devices import get_user_device_directory
from app.shared.clock import now_bogota
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)
FCM_PATH = "/users/me/fcm-token"


@pytest.fixture(autouse=True)
def _clean(clean_db) -> None:
    """Cada prueba arranca con las tablas vacías."""


def _register() -> str:
    email = f"device-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post(
        "/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT}
    )
    assert created.status_code == 201, created.text
    return email


def _login(email: str) -> dict[str, str]:
    login = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _user_id(headers: dict[str, str]) -> uuid.UUID:
    return uuid.UUID(client.get("/users/me", headers=headers).json()["id"])


def _stored_fcm_tokens(clean_db) -> list[str | None]:
    with clean_db() as db:
        return list(db.scalars(text("SELECT fcm_token FROM sessions ORDER BY created_at")))


def test_register_fcm_token_associates_it_with_the_current_session():
    """RF-NOT-01: la app registra el token FCM después de iniciar sesión."""
    headers = _login(_register())

    response = client.put(FCM_PATH, json={"fcm_token": "token-a"}, headers=headers)

    assert response.status_code == 204
    assert get_user_device_directory().get_fcm_tokens(_user_id(headers)) == ["token-a"]


def test_user_can_have_several_devices():
    """RF-NOT-01: un usuario puede tener varios dispositivos."""
    email = _register()
    phone, laptop = _login(email), _login(email)

    client.put(FCM_PATH, json={"fcm_token": "token-phone"}, headers=phone)
    client.put(FCM_PATH, json={"fcm_token": "token-laptop"}, headers=laptop)

    tokens = get_user_device_directory().get_fcm_tokens(_user_id(phone))
    assert sorted(tokens) == ["token-laptop", "token-phone"]


def test_registering_again_replaces_the_session_token():
    headers = _login(_register())
    client.put(FCM_PATH, json={"fcm_token": "token-viejo"}, headers=headers)

    client.put(FCM_PATH, json={"fcm_token": "token-nuevo"}, headers=headers)

    assert get_user_device_directory().get_fcm_tokens(_user_id(headers)) == ["token-nuevo"]


def test_token_already_in_another_session_moves_to_the_current_one():
    """UNIQUE (fcm_token): el mismo dispositivo inicia sesión con otra cuenta."""
    first, second = _login(_register()), _login(_register())
    client.put(FCM_PATH, json={"fcm_token": "token-compartido"}, headers=first)

    response = client.put(FCM_PATH, json={"fcm_token": "token-compartido"}, headers=second)

    assert response.status_code == 204
    directory = get_user_device_directory()
    assert directory.get_fcm_tokens(_user_id(first)) == []
    assert directory.get_fcm_tokens(_user_id(second)) == ["token-compartido"]


def test_remove_fcm_token_clears_it():
    """RF-NOT-01: la app puede quitar el token del dispositivo."""
    headers = _login(_register())
    client.put(FCM_PATH, json={"fcm_token": "token-a"}, headers=headers)

    response = client.delete(FCM_PATH, headers=headers)

    assert response.status_code == 204
    assert get_user_device_directory().get_fcm_tokens(_user_id(headers)) == []


def test_logout_sets_the_fcm_token_to_null(clean_db):
    """RF-USR-04: al cerrar sesión se elimina el token FCM de esa sesión."""
    headers = _login(_register())
    user_id = _user_id(headers)
    client.put(FCM_PATH, json={"fcm_token": "token-a"}, headers=headers)

    assert client.post("/users/logout", headers=headers).status_code == 204

    assert _stored_fcm_tokens(clean_db) == [None]
    assert get_user_device_directory().get_fcm_tokens(user_id) == []


@pytest.mark.parametrize("method", ["put", "delete"])
def test_fcm_token_routes_require_authentication(method):
    response = client.request(method, FCM_PATH, json={"fcm_token": "token-a"})

    assert response.status_code == 401


@pytest.mark.parametrize("fcm_token", ["", "   "])
def test_empty_fcm_token_is_rejected(fcm_token):
    headers = _login(_register())

    response = client.put(FCM_PATH, json={"fcm_token": fcm_token}, headers=headers)

    assert response.status_code == 422


def test_invalidate_fcm_token_sets_it_to_null():
    """Diccionario 5.2: si FCM reporta un token inválido, Usuario lo pone en NULL."""
    headers = _login(_register())
    client.put(FCM_PATH, json={"fcm_token": "token-invalido"}, headers=headers)
    directory = get_user_device_directory()

    directory.invalidate_fcm_token("token-invalido")

    assert directory.get_fcm_tokens(_user_id(headers)) == []


def test_is_active_reflects_deactivated_at(clean_db):
    """RF-USR-09: la cuenta está activa si `deactivated_at IS NULL`."""
    headers = _login(_register())
    user_id = _user_id(headers)
    directory = get_user_device_directory()
    assert directory.is_active(user_id) is True

    users = SqlAlchemyUserRepository(clean_db)
    user = users.get_by_id(user_id)
    user.deactivated_at = now_bogota()
    users.save(user)

    assert directory.is_active(user_id) is False
    assert directory.is_active(uuid.uuid4()) is False


def test_in_memory_repository_follows_the_same_fcm_rules():
    """El doble en memoria cumple las mismas reglas que PostgreSQL (RF-NOT-01)."""
    sessions = InMemorySessionRepository()
    owner, other = uuid.uuid4(), uuid.uuid4()
    first, second = uuid.uuid4(), uuid.uuid4()
    sessions.create(first, owner, "refresh-1", now_bogota())
    sessions.create(second, other, "refresh-2", now_bogota())

    sessions.set_fcm_token(first, "token-a")
    sessions.set_fcm_token(second, "token-a")
    assert sessions.get_fcm_tokens(owner) == []
    assert sessions.get_fcm_tokens(other) == ["token-a"]

    sessions.clear_fcm_token(second)
    assert sessions.get_fcm_tokens(other) == []

    sessions.set_fcm_token(first, "token-b")
    sessions.revoke(first, now_bogota())
    sessions.set_fcm_token(first, "token-c")
    assert sessions.get_fcm_tokens(owner) == []
