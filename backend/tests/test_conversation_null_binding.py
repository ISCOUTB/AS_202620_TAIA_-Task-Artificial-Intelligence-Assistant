"""Regresión del 500 real: ausencia de acción debe ser SQL NULL, no JSON null."""
from psycopg.types.json import Jsonb
from sqlalchemy.dialects.postgresql.psycopg import dialect

from app.modules.ai.adapters.outbound.sqlalchemy_models import ConversationModel


def test_absent_pending_action_binds_to_sql_null():
    column = ConversationModel.__table__.c.pending_action
    pg = dialect()
    processor = column.type.dialect_impl(pg).bind_processor(pg)
    assert processor(None) is None, "JSON null viola pending_action_consistent cuando expires_at es SQL NULL"


def test_pending_action_still_binds_to_a_json_object():
    column = ConversationModel.__table__.c.pending_action
    pg = dialect()
    bound = column.type.dialect_impl(pg).bind_processor(pg)({"kind": "create_task"})
    assert isinstance(bound, Jsonb)
    assert bound.obj == {"kind": "create_task"}
