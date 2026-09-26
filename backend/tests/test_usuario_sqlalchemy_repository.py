"""Pruebas de integración del repositorio de Usuario contra PostgreSQL (RNF-06, RT-03).

Requieren TEST_DATABASE_URL apuntando a una base de datos de pruebas vacía.
Sin esa variable se omiten.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import BOGOTA_TZ

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL no está configurada.")

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture(scope="module")
def session_factory():
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    config = Config(str(ALEMBIC_INI))
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        # Falla si los modelos ORM y las migraciones no coinciden.
        command.check(config)
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous

    engine = create_engine(TEST_DATABASE_URL)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def repository(session_factory):
    with session_factory.begin() as session:
        session.execute(text("TRUNCATE users"))
    return SqlAlchemyUserRepository(session_factory)


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
