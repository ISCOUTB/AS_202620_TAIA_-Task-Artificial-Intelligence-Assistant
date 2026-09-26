"""Conexión a PostgreSQL compartida por los adaptadores de persistencia (RNF-06).

Cada módulo define sus modelos ORM sobre `Base` en sus propios adaptadores de
salida. El dominio nunca importa este archivo.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from pathlib import Path
from functools import lru_cache

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path(__file__).resolve().parents[4] / ".env")


class Base(DeclarativeBase):
    """Base declarativa de todos los modelos ORM de TAIA."""

    # Nombres estables para que Alembic genere migraciones reproducibles.
    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
        }
    )


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("La variable de entorno DATABASE_URL no está configurada.")
    return url


@lru_cache
def get_engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
