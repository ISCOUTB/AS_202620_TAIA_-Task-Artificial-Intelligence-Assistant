"""Configuración común de las pruebas.

Las pruebas unitarias y de API usan los repositorios en memoria. Debe
definirse antes de importar la aplicación, porque los proveedores eligen el
repositorio al importarse.

Las pruebas de integración usan la fixture `db_session_factory`, que aplica
todas las migraciones sobre TEST_DATABASE_URL. Sin esa variable se omiten.
"""

import os
from pathlib import Path

import pytest

os.environ["TAIA_STORAGE"] = "memory"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture(scope="session")
def db_session_factory():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL no está configurada.")

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

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
def clean_db(db_session_factory):
    """Vacía todas las tablas de datos antes de cada prueba de integración."""

    from sqlalchemy import text

    with db_session_factory.begin() as session:
        session.execute(text("TRUNCATE users, subjects, academic_periods CASCADE"))
    return db_session_factory
