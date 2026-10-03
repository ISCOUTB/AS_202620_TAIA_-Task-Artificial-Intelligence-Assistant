"""Integridad del dataset de evaluacion del modelo (S1).

Estas pruebas no necesitan GEMINI_API_KEY: comprueban que el dataset que
consume `tools/eval_llm.py` sigue siendo valido y representativo. Si el dominio
cambia una intencion o el dataset se queda sin cobertura, el CI lo detecta sin
tener que gastar una llamada al proveedor.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from app.modules.ai.domain.messages import Intent

DATASET = Path(__file__).resolve().parents[2] / "docs" / "evaluacion_ia" / "dataset.jsonl"
MINIMO_POR_INTENCION = 3


def _filas() -> list[dict]:
    return [
        json.loads(linea)
        for linea in DATASET.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]


def test_dataset_existe_y_no_esta_vacio():
    assert DATASET.is_file(), "falta el dataset de evaluacion"
    assert _filas(), "el dataset esta vacio"


def test_todas_las_lineas_son_json_valido():
    for numero, linea in enumerate(DATASET.read_text(encoding="utf-8").splitlines(), 1):
        if not linea.strip():
            continue
        try:
            json.loads(linea)
        except ValueError as error:
            pytest.fail("dataset linea {}: JSON invalido: {}".format(numero, error))


def test_cada_caso_tiene_los_campos_obligatorios():
    for fila in _filas():
        assert {"id", "text", "intent", "note"} <= set(fila), fila


def test_las_intenciones_existen_en_el_dominio():
    validas = {i.value for i in Intent}
    for fila in _filas():
        assert fila["intent"] in validas, fila


def test_los_identificadores_no_se_repiten():
    ids = [f["id"] for f in _filas()]
    repetidos = [i for i, n in Counter(ids).items() if n > 1]
    assert not repetidos, repetidos


def test_cada_intencion_tiene_suficientes_casos():
    conteo = Counter(f["intent"] for f in _filas())
    escasas = {i: n for i, n in conteo.items() if n < MINIMO_POR_INTENCION}
    assert not escasas, "con menos de {} casos la metrica no es fiable: {}".format(
        MINIMO_POR_INTENCION, escasas
    )


def test_se_cubren_todas_las_intenciones_del_dominio():
    """Sin casos para una intencion, el modelo puede fallar sin que se note."""

    cubiertas = {f["intent"] for f in _filas()}
    faltantes = {i.value for i in Intent} - cubiertas
    assert not faltantes, "intenciones sin ningun caso: {}".format(sorted(faltantes))


def test_el_dataset_conserva_la_variedad_ortografica_del_defecto():
    """La razon de ser del dataset: no repetir solo la forma canonica."""

    textos = [f["text"] for f in _filas()]
    assert any("¿" in t for t in textos), "sin preguntas con tilde inicial"
    assert any(t.isupper() for t in textos), "sin mensajes en mayusculas"
    assert any("!" in t or "," in t for t in textos), "sin signos intercalados"


def test_hay_casos_de_unknown_que_no_deben_confundirse():
    """Un `unknown` erroneo se paga como una tarea creada de mas."""

    desconocidos = [f for f in _filas() if f["intent"] == "unknown"]
    assert len(desconocidos) >= MINIMO_POR_INTENCION
    for fila in desconocidos:
        assert fila["note"], "todo caso unknown debe explicar por que lo es"