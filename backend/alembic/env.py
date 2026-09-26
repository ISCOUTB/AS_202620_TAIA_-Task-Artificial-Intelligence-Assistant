"""Entorno de migraciones de Alembic.

Importa los modelos ORM de todos los módulos para que `--autogenerate`
compare la base de datos con `Base.metadata`. Al crear un modelo nuevo en un
módulo, se agrega su import aquí.
"""

from alembic import context
from sqlalchemy import create_engine, pool

from app.shared.adapters.outbound.database import Base, database_url

import app.modules.academic.adapters.outbound.sqlalchemy_models  # noqa: F401
import app.modules.ai.adapters.outbound.sqlalchemy_models  # noqa: F401
import app.modules.reminders.adapters.outbound.sqlalchemy_models  # noqa: F401
import app.modules.usuario.adapters.outbound.sqlalchemy_models  # noqa: F401
import app.modules.usuario.adapters.outbound.sqlalchemy_user_repository  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
