"""El evaluador no debe confundir una intención correcta con campos correctos."""

import importlib.util
from pathlib import Path
from datetime import datetime

from app.modules.ai.domain.messages import Interpretation, Intent, ExtractedTaskData

SPEC = importlib.util.spec_from_file_location(
    "eval_llm", Path(__file__).resolve().parents[2] / "tools/eval_llm.py")
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)


def test_wrong_fields_are_counted_even_when_intent_matches():
    row = {"intent": "create_task", "title": "Ensayo", "subject": "Física",
           "due_at": "2026-10-09T17:00:00-05:00"}
    result = Interpretation(Intent.CREATE_TASK, 1, task=ExtractedTaskData(
        title="Otro título", subject="Física",
        due_at=datetime.fromisoformat("2026-10-09T22:00:00+00:00")))
    fields = evaluator.comparar_campos(row, result)
    assert [f["correcto"] for f in fields] == [False, True, True]


def test_error_does_not_count_null_fields_as_correct():
    assert not evaluator.comparar_campos({"intent": "create_task", "title": None}, None)[0]["correcto"]


def test_evaluation_excludes_empty_and_counts_provider_failure(monkeypatch):
    class Provider:
        closed = False
        calls = 0

        def interpret(self, request, now):
            self.calls += 1
            if request.text == "error":
                raise RuntimeError("secret material must never be exported")
            return Interpretation(Intent.CREATE_TASK, 1,
                                  task=ExtractedTaskData(title="Incorrecto"))

        def last_usage(self):
            return None

        def close(self):
            self.closed = True

    provider = Provider()
    monkeypatch.setattr(evaluator.GeminiLLM, "from_env", lambda: provider)
    monkeypatch.setattr(evaluator.time, "sleep", lambda _: None)
    rows = [{"id": "empty", "text": "", "intent": "unknown"},
            {"id": "one", "text": "crear", "intent": "create_task", "title": "Ensayo"},
            {"id": "two", "text": "error", "intent": "create_task", "title": "Taller"}]
    result = evaluator.evaluar(rows, None, None)
    assert provider.calls == 2 and provider.closed
    assert result["S1_exactitud_intencion"] == 0.5
    assert result["S1_campos"]["esperados"] == 2
    assert result["S1_campos"]["correctos"] == 0
    assert result["S1_campos"]["supera_umbral_extraccion"] is False
    assert result["S1_campos"]["cumple_escenario"] is None
    assert result["S3_latencia_ms"]["muestras"] == 2
    assert result["S3_latencia_ms"]["errores"] == 1
    assert result["S3_latencia_ms"]["cumple_escenario"] is None
    assert result["S5_tokens"]["costo_usd"] is None
    assert "secret material" not in str(result)
