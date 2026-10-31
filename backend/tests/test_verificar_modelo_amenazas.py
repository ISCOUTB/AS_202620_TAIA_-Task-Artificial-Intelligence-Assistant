"""El verificador del modelo de amenazas debe detectar huecos, no solo leer tablas."""

from __future__ import annotations

import importlib.util
from pathlib import Path

# Se carga por ruta, igual que las demas pruebas de herramientas del repositorio.
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verificar_modelo_amenazas", ROOT / "tools/verificar_modelo_amenazas.py"
)
verificador = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verificador)


DOCUMENTO = """## 2. Amenazas priorizadas

| ID | Elemento C4 | STRIDE | OWASP | Amenaza | P | I | Prio. |
|---|---|---|---|---|---|---|---|
| T-01 | API TAIA | Spoofing | A07 | Fuerza bruta | 3 | 3 | 9 |
| T-02 | API TAIA | Tampering | A03 | Inyeccion | 2 | 1 | 2 |

## 3. Plan de mitigacion

| ID | Mitigacion | Dueno | Estado | Evidencia | Residual |
|---|---|---|---|---|---|
| T-01 | Limite de intentos | mark | Hecha | `abc1234` | Bajo |
| T-02 | Reglas del prompt | val | Pendiente | [prueba](prueba.md) | Medio |

## 4. Otra seccion
"""


def analizar(tmp_path: Path, documento: str = DOCUMENTO) -> dict:
    (tmp_path / "prueba.md").write_text("evidencia", encoding="utf-8")
    return verificador.analizar(documento, tmp_path)


def test_documento_completo_pasa(tmp_path):
    resultado = analizar(tmp_path)

    assert resultado["problemas"] == []
    assert resultado["veredicto"] == "ok"
    assert resultado["amenazas"] == 2
    assert resultado["mitigaciones"] == 2
    assert resultado["por_prioridad"] == {"2": 1, "9": 1}
    assert resultado["por_estado"] == {"Hecha": 1, "Pendiente": 1}
    assert resultado["por_residual"] == {"Bajo": 1, "Medio": 1}


def test_amenaza_sin_fila_de_mitigacion(tmp_path):
    documento = DOCUMENTO.replace(
        "| T-02 | Reglas del prompt | val | Pendiente | [prueba](prueba.md) | Medio |\n", ""
    )

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-02 no tiene fila de mitigacion" in problema for problema in problemas)


def test_mitigacion_sin_amenaza(tmp_path):
    documento = DOCUMENTO.replace(
        "| T-02 | Reglas del prompt | val | Pendiente | [prueba](prueba.md) | Medio |",
        "| T-02 | Reglas del prompt | val | Pendiente | [prueba](prueba.md) | Medio |\n"
        "| T-99 | Huerfana | mark | Hecha | `abc1234` | Bajo |",
    )

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-99 no corresponde a ninguna amenaza" in problema for problema in problemas)


def test_prioridad_distinta_de_probabilidad_por_impacto(tmp_path):
    documento = DOCUMENTO.replace("| 3 | 3 | 9 |", "| 3 | 3 | 8 |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-01: la prioridad '8' no es P x I" in problema for problema in problemas)


def test_probabilidad_fuera_de_rango(tmp_path):
    documento = DOCUMENTO.replace("| 3 | 3 | 9 |", "| 4 | 3 | 9 |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-01: P debe ser 1, 2 o 3" in problema for problema in problemas)


def test_tabla_desordenada(tmp_path):
    documento = DOCUMENTO.replace(
        "| T-01 | API TAIA | Spoofing | A07 | Fuerza bruta | 3 | 3 | 9 |\n"
        "| T-02 | API TAIA | Tampering | A03 | Inyeccion | 2 | 1 | 2 |",
        "| T-02 | API TAIA | Tampering | A03 | Inyeccion | 2 | 1 | 2 |\n"
        "| T-01 | API TAIA | Spoofing | A07 | Fuerza bruta | 3 | 3 | 9 |",
    )

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("rompe el orden" in problema for problema in problemas)


def test_estado_no_reconocido(tmp_path):
    documento = DOCUMENTO.replace("| val | Pendiente |", "| val | En revision |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-02: estado no reconocido 'En revision'" in problema for problema in problemas)


def test_riesgo_residual_no_reconocido(tmp_path):
    documento = DOCUMENTO.replace("| Pendiente | [prueba](prueba.md) | Medio |", "| Pendiente | [prueba](prueba.md) | Critico |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-02: riesgo residual no reconocido 'Critico'" in problema for problema in problemas)


def test_categoria_stride_no_reconocida(tmp_path):
    documento = DOCUMENTO.replace("| Spoofing |", "| Suplantacion |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-01: categoria STRIDE no reconocida 'Suplantacion'" in p for p in problemas)


def test_referencia_owasp_no_reconocida(tmp_path):
    documento = DOCUMENTO.replace("| A07 |", "| A11 |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-01: referencia OWASP no reconocida 'A11'" in p for p in problemas)


def test_evidencia_con_enlace_inexistente(tmp_path):
    documento = DOCUMENTO.replace("[prueba](prueba.md)", "[prueba](no-existe.md)")

    resultado = analizar(tmp_path, documento)

    assert any("T-02: la evidencia 'no-existe.md' no existe" in p for p in resultado["problemas"])
    assert resultado["evidencias_inexistentes"] == [{"id": "T-02", "enlace": "no-existe.md"}]


def test_evidencia_vacia(tmp_path):
    documento = DOCUMENTO.replace("| [prueba](prueba.md) |", "| |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-02: la evidencia debe citar un archivo o un commit" in p for p in problemas)


def test_id_duplicado(tmp_path):
    documento = DOCUMENTO.replace(
        "| T-02 | API TAIA | Tampering | A03 | Inyeccion | 2 | 1 | 2 |",
        "| T-01 | API TAIA | Tampering | A03 | Inyeccion | 2 | 1 | 2 |",
    )

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("T-01 aparece mas de una vez" in problema for problema in problemas)


def test_columna_obligatoria_faltante(tmp_path):
    documento = DOCUMENTO.replace("| ID | Mitigacion | Dueno | Estado | Evidencia |", "| ID | Mitigacion | Dueno | Estado |")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("faltan columnas: evidencia" in problema for problema in problemas)


def test_seccion_ausente(tmp_path):
    documento = DOCUMENTO.replace("## 3. Plan de mitigacion", "## 3. Otro titulo")

    problemas = analizar(tmp_path, documento)["problemas"]

    assert any("no se encontro la seccion '## 3. Plan de mitigacion'" in p for p in problemas)


def test_documento_del_repositorio_es_consistente():
    """Regresion sobre el documento real: si alguien rompe una fila, CI falla."""

    resultado = verificador.analizar(
        verificador.DOC.read_text(encoding="utf-8"),
        verificador.DOC.parent,
        "docs/modelo_amenazas.md",
    )

    assert resultado["problemas"] == []
    assert resultado["amenazas"] == resultado["mitigaciones"]
    assert resultado["amenazas"] > 0
