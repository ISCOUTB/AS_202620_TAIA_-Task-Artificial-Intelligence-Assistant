"""Mutación en memoria del mapeo JSONB; salida esperada: 1 failed, 1 passed.

No conecta a PostgreSQL ni cambia archivos. Ejecutar sin TEST_DATABASE_URL.
"""
import os
from pathlib import Path
import sys

import pytest
from sqlalchemy.dialects.postgresql import JSONB

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


if __name__ == "__main__":
    if os.getenv("TEST_DATABASE_URL"):
        raise SystemExit("Ejecutar sin TEST_DATABASE_URL: esta demostración no usa base de datos.")
    from app.modules.ai.adapters.outbound.sqlalchemy_models import ConversationModel

    # Reintroduce únicamente el defecto observado, durante este proceso.
    ConversationModel.__table__.c.pending_action.type = JSONB(none_as_null=False)
    raise SystemExit(pytest.main([
        str(ROOT / "backend/tests/test_conversation_null_binding.py"),
        "-q", "-p", "no:cacheprovider",
    ]))
