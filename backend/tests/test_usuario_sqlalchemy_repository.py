"""Pruebas de integración del repositorio de Usuario contra PostgreSQL (RNF-06, RT-03).

Usan la fixture `clean_db` de conftest.py; sin TEST_DATABASE_URL se omiten.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import BOGOTA_TZ


@pytest.fixture
def repository(clean_db):
    return SqlAlchemyUserRepository(clean_db)


def _new_user(email: str = "ana@example.com") -> Usuario:
    return Usuario.create(full_name="Ana Pérez", email=Email(email), password_hash="hash")


def test_add_and_get_by_id_round_trip(repository):
    user = _new_user()
    repository.add(user)

    stored = repository.get_by_id(user.id)

    assert stored is not None
    assert stored.full_name == "Ana Pérez"
    assert stored.email == Email("ana@example.com")
    assert stored.telegram_user_id is None
    assert stored.deactivated_at is None


def test_dates_are_returned_in_bogota_time(repository):
    user = _new_user()
    repository.add(user)

    stored = repository.get_by_id(user.id)

    assert stored.created_at.utcoffset() == BOGOTA_TZ.utcoffset(None)
    assert stored.created_at == user.created_at


def test_get_by_email(repository):
    user = _new_user("luis@example.com")
    repository.add(user)

    assert repository.get_by_email(Email("LUIS@example.com")).id == user.id
    assert repository.get_by_email(Email("otro@example.com")) is None


def test_save_persists_telegram_link(repository):
    user = _new_user()
    repository.add(user)

    user.link_telegram(123456, now=datetime(2026, 10, 1, 8, 30, tzinfo=BOGOTA_TZ))
    repository.save(user)

    stored = repository.get_by_telegram_user_id(123456)
    assert stored.id == user.id
    assert stored.telegram_linked_at == datetime(2026, 10, 1, 8, 30, tzinfo=BOGOTA_TZ)


def test_get_missing_user_returns_none(repository):
    assert repository.get_by_id(uuid.uuid4()) is None


def test_email_is_unique(repository):
    repository.add(_new_user())

    with pytest.raises(IntegrityError):
        repository.add(_new_user())
