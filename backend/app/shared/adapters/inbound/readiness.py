"""Comprobación local de disponibilidad: no hace llamadas pagadas al LLM."""

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.shared.adapters.outbound.database import get_engine


def require_database() -> None:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # Las excepciones del driver pueden contener la URL o datos del servidor.
        raise HTTPException(status_code=503, detail="Base de datos no disponible.") from None
