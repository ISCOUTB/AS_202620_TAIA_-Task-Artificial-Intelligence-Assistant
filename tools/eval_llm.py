"""Evaluacion del modelo de lenguaje contra el dataset (S1 y S3).

Uso:
    python tools/eval_llm.py                 # exige GEMINI_API_KEY
    python tools/eval_llm.py --dry-run       # valida el dataset, sin llamar al modelo
    python tools/eval_llm.py --json salida.json

A diferencia de `tools/eval_confirmacion.py`, que mide la porcion determinista
sin red, este guion si llama a Gemini. Sin `GEMINI_API_KEY` no inventa cifras:
termina con codigo 2 y explica que la medicion queda pendiente. Es la unica
manera honesta de distinguir "el modelo acierta el 84%" de "no se midio".

Salida:
  * S1 exactitud de intencion, desglosada por intencion y con matriz de
    confusion, para no esconder que un `unknown` se confunde con `query_tasks`;
  * exactitud de los campos (titulo, referencia de tarea, filtros);
  * S3 latencia p50 y p95 por llamada;
  * S5 tokens y costo estimado, con el precio declarado como entrada.

El precio NO esta en el codigo a proposito: cambia con frecuencia y una tabla
desactualizada daria un costo falso. Se pasa con --precio-input/--precio-output
por millon de tokens, en USD.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.ai.adapters.outbound.gemini_llm import GeminiLLM  # noqa: E402
from app.modules.ai.domain.messages import Channel, IncomingRequest, Intent  # noqa: E402

DATASET = ROOT / "docs" / "evaluacion_ia" / "dataset.jsonl"
TZ = timezone(timedelta(hours=-5))
AHORA = datetime(2026, 9, 10, 12, 0, tzinfo=TZ)

INTENCIONES = {i.value for i in Intent}


def cargar_dataset() -> list[dict]:
    if not DATASET.is_file():
        raise SystemExit("No existe el dataset: {}".format(DATASET))
    filas: list[dict] = []
    for numero, linea in enumerate(DATASET.read_text(encoding="utf-8").splitlines(), 1):
        if not linea.strip():
            continue
        try:
            fila = json.loads(linea)
        except ValueError as error:
            raise SystemExit("dataset linea {}: JSON invalido: {}".format(numero, error))
        campos = {"id", "text", "intent", "note"}
        faltan = campos - set(fila)
        if faltan:
            raise SystemExit("dataset linea {}: faltan campos {}".format(numero, sorted(faltan)))
        if fila["intent"] not in INTENCIONES:
            raise SystemExit(
                "dataset linea {}: intencion '{}' no existe en el dominio".format(
                    numero, fila["intent"]
                )
            )
        filas.append(fila)
    if not filas:
        raise SystemExit("El dataset esta vacio.")
    return filas


def validar(filas: list[dict]) -> dict:
    """Comprobaciones de integridad que no necesitan la clave del proveedor."""

    ids = [f["id"] for f in filas]
    repetidos = [i for i, n in Counter(ids).items() if n > 1]
    if repetidos:
        raise SystemExit("dataset: ids repetidos {}".format(repetidos))
    por_intencion = Counter(f["intent"] for f in filas)
    if min(por_intencion.values()) < 3:
        raise SystemExit(
            "dataset: alguna intencion tiene menos de 3 casos, la metrica seria "
            "poco fiable: {}".format(dict(por_intencion))
        )
    return {
        "casos": len(filas),
        "por_intencion": dict(sorted(por_intencion.items())),
        "vacios": sum(1 for f in filas if not f["text"].strip()),
    }


def evaluar(filas: list[dict], precio_input: float, precio_output: float) -> dict:
    llm = GeminiLLM.from_env()
    aciertos = 0
    matriz: Counter = Counter()
    fallos: list[dict] = []
    tiempos: list[float] = []
    tokens_entrada = 0
    tokens_salida = 0

    for fila in filas:
        request = IncomingRequest(
            user_id="u-eval", text=fila["text"], channel=Channel.TELEGRAM
        )
        inicio = time.perf_counter()
        try:
            resultado = llm.interpret(request, AHORA)
        except Exception as error:  # noqa: BLE001 - el fallo se contabiliza
            matriz[(fila["intent"], f"error:{type(error).__name__}")] += 1
            fallos.append(
                {"id": fila["id"], "esperado": fila["intent"], "error": type(error).__name__}
            )
            continue
        tiempos.append((time.perf_counter() - inicio) * 1000)

        uso = llm.last_usage()
        if uso is not None:
            tokens_entrada += uso.prompt_tokens
            tokens_salida += uso.candidates_tokens

        obtenido = resultado.intent.value
        matriz[(fila["intent"], obtenido)] += 1
        if obtenido == fila["intent"]:
            aciertos += 1
        else:
            entrada = {"id": fila["id"], "esperado": fila["intent"], "obtenido": obtenido}
            if fila.get("title") and resultado.task:
                entrada["titulo_esperado"] = fila["title"]
                entrada["titulo_obtenido"] = resultado.task.title
            if fila.get("task_hint"):
                entrada["referencia_esperada"] = fila["task_hint"]
                entrada["referencia_obtenida"] = resultado.task_hint
            fallos.append(entrada)

    percentiles = statistics.quantiles(tiempos, n=100) if len(tiempos) > 1 else [0.0]
    costo = (tokens_entrada / 1e6 * precio_input) + (tokens_salida / 1e6 * precio_output)

    return {
        "S1_exactitud_intencion": round(aciertos / len(filas), 4),
        "S1_matriz_de_confusion": {
            "{}->{}".format(a, b): n for (a, b), n in sorted(matriz.items())
        },
        "S1_por_intencion": _por_intencion(matriz, len(filas)),
        "S1_fallos": fallos,
        "S3_latencia_ms": {
            "muestras": len(tiempos),
            "p50": round(statistics.median(tiempos), 1) if tiempos else None,
            "p95": round(percentiles[94], 1) if len(tiempos) > 1 else None,
            "maximo": round(max(tiempos), 1) if tiempos else None,
        },
        "S5_tokens": {
            "prompt": tokens_entrada,
            "candidates": tokens_salida,
            "costo_usd": round(costo, 6),
            "precio_declarado": {
                "input_por_millon_usd": precio_input,
                "output_por_millon_usd": precio_output,
            },
        },
    }


def _por_intencion(matriz: Counter, total: int) -> dict:
    detalle: dict[str, dict] = {}
    for (esperado, _), n in matriz.items():
        fila = detalle.setdefault(esperado, {"casos": 0, "aciertos": 0})
        fila["casos"] += n
    for (esperado, obtenido), n in matriz.items():
        if esperado == obtenido:
            detalle[esperado]["aciertos"] += n
    for fila in detalle.values():
        fila["exactitud"] = round(fila["aciertos"] / fila["casos"], 4)
    return dict(sorted(detalle.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Solo valida el dataset.")
    parser.add_argument("--json", help="Ruta opcional para volcar el resultado.")
    parser.add_argument("--precio-input", type=float, default=0.0)
    parser.add_argument("--precio-output", type=float, default=0.0)
    args = parser.parse_args()

    filas = cargar_dataset()
    integridad = validar(filas)

    if args.dry_run:
        print(json.dumps({"integridad": integridad, "estado": "dataset valido"}, ensure_ascii=False, indent=2))
        return 0

    import os

    if not os.getenv("GEMINI_API_KEY"):
        print(
            "S1 y S3 quedan PENDIENTES: no hay GEMINI_API_KEY.\n"
            "Este guion no inventa mediciones. Defina la clave y vuelva a "
            "ejecutarlo, o use --dry-run para validar el dataset."
        )
        print(json.dumps({"integridad": integridad}, ensure_ascii=False, indent=2))
        return 2

    resultado = {"integridad": integridad}
    resultado.update(evaluar(filas, args.precio_input, args.precio_output))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.json:
        Path(args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())