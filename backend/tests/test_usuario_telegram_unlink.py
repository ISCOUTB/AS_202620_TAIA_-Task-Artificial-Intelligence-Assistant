"""Desvincular Telegram desde la aplicación (RF-TEL-03)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.application.ports.inbound.identity import get_identity_service
from app.modules.usuario.application.use_cases.link_telegram import UnlinkTelegramUseCase
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from tests.helpers import register_and_login

client = TestClient(app)
UNLINK_PATH = "/users/me/telegram"
TELEGRAM_USER_ID = 123123123


@pytest.fixture(autouse=True)
def _clean(clean_db) -> None:
    """Cada prueba arranca con las tablas vacías."""


def _linked_user(clean_db) -> tuple[dict[str, str], uuid.UUID]:
    headers = register_and_login(client)
    user_id = uuid.UUID(client.get("/users/me", headers=headers).json()["id"])
    users = SqlAlchemyUserRepository(clean_db)
    user = users.get_by_id(user_id)
    user.link_telegram(TELEGRAM_USER_ID)
    users.save(user)
    return headers, user_id


def test_unlink_clears_both_telegram_columns(clean_db):
    """RF-TEL-03: `telegram_user_id` y `telegram_linked_at` quedan en NULL."""
    headers, user_id = _linked_user(clean_db)

    response = client.delete(UNLINK_PATH, headers=headers)

    assert response.status_code == 204
    stored = SqlAlchemyUserRepository(clean_db).get_by_id(user_id)
    assert stored.telegram_user_id is None
    assert stored.telegram_linked_at is None
    assert client.get("/users/me", headers=headers).json()["telegram_linked"] is False


def test_unlinked_telegram_account_no_longer_resolves_to_the_user(clean_db):
    """RF-TEL-03: después, los mensajes desde esa cuenta de Telegram ya no tienen acceso a sus datos."""
    headers, user_id = _linked_user(clean_db)
    users = SqlAlchemyUserRepository(clean_db)
    assert users.get_by_telegram_user_id(TELEGRAM_USER_ID).id == user_id

    client.delete(UNLINK_PATH, headers=headers)

    assert users.get_by_telegram_user_id(TELEGRAM_USER_ID) is None
    assert get_identity_service().get_telegram_user_id(user_id) is None


def test_unlink_requires_authentication():
    """RF-TEL-03 y RT-01: la ruta exige JWT."""
    assert client.delete(UNLINK_PATH).status_code == 401


def test_unlink_without_a_link_is_a_no_op():
    """RF-TEL-03: desvincular una cuenta sin Telegram no cambia nada y responde 204."""
    headers = register_and_login(client)

    assert client.delete(UNLINK_PATH, headers=headers).status_code == 204
    assert client.get("/users/me", headers=headers).json()["telegram_linked"] is False


def test_in_memory_repository_stops_resolving_after_unlinking():
    """RF-TEL-03: el doble en memoria aplica la misma regla."""
    users = InMemoryUserRepository()
    user = Usuario.create("Ana", Email("ana@example.com"), "hash")
    user.link_telegram(TELEGRAM_USER_ID)
    users.add(user)

    UnlinkTelegramUseCase(users).execute(user.id)

    assert users.get_by_telegram_user_id(TELEGRAM_USER_ID) is None
