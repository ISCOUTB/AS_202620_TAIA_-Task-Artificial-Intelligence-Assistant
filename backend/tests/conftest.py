"""Configuración común de las pruebas de integración con PostgreSQL.

La fixture `db_session_factory` aplica todas las migraciones sobre
TEST_DATABASE_URL. Sin esa variable, las pruebas que la solicitan se omiten.
"""

import os
from pathlib import Path

import pytest

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

# RNF-02 exige el secreto JWT; las pruebas usan uno propio.
os.environ.setdefault("TAIA_JWT_SECRET", "test-only-jwt-secret-with-enough-length")

if TEST_DATABASE_URL:
    # Se ejecuta antes de que los módulos de prueba importen app.main.
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Prepara el PostgreSQL de CI antes de que cualquier endpoint lo use."""

    if not TEST_DATABASE_URL:
        yield
        return

    from alembic import command
    from alembic.config import Config

    config = Config(str(ALEMBIC_INI))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.check(config)
    yield


@pytest.fixture(scope="session")
def db_session_factory(migrated_database):
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL no está configurada.")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(TEST_DATABASE_URL)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def clean_db(db_session_factory):
    """Vacía todas las tablas de datos antes de cada prueba de integración."""

    from sqlalchemy import text

    with db_session_factory.begin() as session:
        session.execute(
            text(
                "TRUNCATE users, subjects, academic_periods, failed_login_attempts, "
                "study_plans, reminders, conversations CASCADE"
            )
        )
    return db_session_factory
