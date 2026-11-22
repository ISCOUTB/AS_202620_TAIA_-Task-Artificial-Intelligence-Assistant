"""Contrato de interpretacion comun a Groq y Gemini (`interpretation_contract.py`).

La validacion de la salida del LLM es la misma para los dos proveedores, asi que
se prueba aqui una vez; los esquemas y la configuracion de cada proveedor se
prueban con `MockTransport` en `test_ai_gemini_llm.py` y `test_ai_groq_llm.py`.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest

from app.modules.ai.adapters.outbound.interpretation_contract import (
    HELP_INSTRUCTIONS,
    KNOWLEDGE_BASE,
    interpretation_instructions,
    parse_interpretation,
)
from app.modules.ai.domain.messages import COLOMBIA_TZ, MAX_GENERATED_TITLE, ExtractedPeriod, Intent

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=COLOMBIA_TZ)


def _parse(**fields):
    return parse_interpretation(json.dumps({"intent": "create_task", "confidence": 0.9} | fields))


@pytest.mark.parametrize("intent", ["complete_task", "summary", "query_schedule"])
def test_new_intents_are_recognized_rf_agt_02(intent):
    assert _parse(intent=intent).intent is Intent(intent)


def test_date_without_time_is_the_end_of_that_day_in_colombia_rf_agt_05():
    task = _parse(task={"title": "Taller", "due_at": "2026-09-11"}).task

    assert task.due_at == datetime(2026, 9, 11, 23, 59, tzinfo=COLOMBIA_TZ)


def test_date_with_time_keeps_it_rf_agt_05():
    task = _parse(task={"title": "Taller", "due_at": "2026-09-11T08:00:00-05:00"}).task

    assert task.due_at == datetime(2026, 9, 11, 8, 0, tzinfo=COLOMBIA_TZ)


@pytest.mark.parametrize(("raw", "expected"), [("exam", "exam"), ("task", "task"), ("quiz", None), (3, None)])
def test_only_task_or_exam_is_accepted_as_type_rf_agt_05(raw, expected):
    result = _parse(task={"title": "Parcial", "type": raw}, filters={"type": raw})

    assert result.task.type == expected
    assert result.filters.type == expected


def test_generated_title_is_cut_to_sixty_characters_on_a_word_rf_agt_06():
    long_title = "Informe de laboratorio de fisica sobre el movimiento rectilineo uniforme"
    task = _parse(task={"title": long_title, "title_generated": True}).task

    assert len(task.title) <= MAX_GENERATED_TITLE
    assert long_title.startswith(task.title)
    assert not task.title.endswith(" ")
    assert task.title_generated is True


def test_title_written_by_the_student_is_not_cut_rf_agt_06():
    """Academic valida el largo de un titulo explicito (RT-06); el contrato no lo recorta."""
    long_title = "x" * 80
    task = _parse(task={"title": long_title, "title_generated": False}).task

    assert task.title == long_title
    assert task.title_generated is False


@pytest.mark.parametrize("flag", ["true", 1, None])
def test_title_generated_must_be_a_real_boolean_rf_agt_06(flag):
    task = _parse(task={"title": "Informe", "title_generated": flag}).task

    assert task.title_generated is False


def test_period_is_read_as_inclusive_days_rf_agt_12():
    result = _parse(intent="summary", period={"start": "2026-09-01", "end": "2026-09-30"})

    assert result.period == ExtractedPeriod(start=date(2026, 9, 1), end=date(2026, 9, 30))


def test_period_with_only_a_start_is_that_day_rf_agt_13():
    result = _parse(intent="query_schedule", period={"start": "2026-09-11T00:00:00-05:00", "end": None})

    assert result.period == ExtractedPeriod(start=date(2026, 9, 11), end=date(2026, 9, 11))


@pytest.mark.parametrize(
    "period",
    [
        {"start": "2026-09-30", "end": "2026-09-01"},
        {"start": None, "end": "2026-09-01"},
        {"start": "manana", "end": None},
        "este mes",
        None,
    ],
)
def test_invalid_period_is_discarded_so_the_agent_asks_rf_agt_12(period):
    assert _parse(intent="summary", period=period).period is None


def test_instructions_cover_the_new_intents_and_rules_rf_agt_05_rf_agt_06():
    rules = interpretation_instructions(NOW)

    for intent in ("complete_task", "summary", "query_schedule"):
        assert f"- {intent}:" in rules
    assert "23:59" in rules
    assert "maximo 60 caracteres" in rules
    assert '"title_generated" en true' in rules
    assert '"period"' in rules
    assert "jueves 2026-09-10T12:00:00-05:00" in rules


def test_instructions_resolve_relative_dates_with_colombia_now_rt_03():
    rules = interpretation_instructions(NOW + timedelta(days=1))

    assert "viernes 2026-09-11T12:00:00-05:00" in rules


def test_help_instructions_carry_the_versioned_knowledge_base_rf_agt_14():
    knowledge = KNOWLEDGE_BASE.read_text(encoding="utf-8").strip()

    assert knowledge in HELP_INSTRUCTIONS
    assert "maximo 3 frases" in HELP_INSTRUCTIONS
    assert "di que no lo sabes" in HELP_INSTRUCTIONS
    assert "solo puedes ayudar con TAIA" in HELP_INSTRUCTIONS
