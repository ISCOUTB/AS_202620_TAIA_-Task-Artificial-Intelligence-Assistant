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
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.ai.adapters.outbound.gemini_llm import GeminiLLM, _DEFAULT_MODEL  # noqa: E402
from app.modules.ai.domain.messages import Channel, IncomingRequest, Intent  # noqa: E402

DATASET = ROOT / "docs" / "evaluacion_ia" / "dataset.jsonl"
TZ = timezone(timedelta(hours=-5))
AHORA = datetime(2026, 9, 10, 12, 0, tzinfo=TZ)

INTENCIONES = {i.value for i in Intent}
PAUSA_ENTRE_LLAMADAS = 6  # segundos; evita el limite por minuto del nivel gratuito


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


def campos_esperados(fila: dict) -> dict:
    """Etiquetas existentes; intención y campos se puntúan por separado."""
    expected = {}
    for key in ("title", "due_at", "subject", "description", "task_hint",
                "status", "due_from", "due_to"):
        if key not in fila:
            continue
        if key == "task_hint":
            path = key
        else:
            parent = "filters" if fila["intent"] == "query_tasks" else "task"
            path = f"{parent}.{key}"
        expected[path] = fila[key]
    return expected


def comparar_campos(fila: dict, resultado) -> list[dict]:
    comparisons = []
    for path, expected in campos_esperados(fila).items():
        actual = resultado
        for part in path.split("."):
            actual = getattr(actual, part, None)
        if isinstance(actual, datetime):
            actual = actual.isoformat()
        if path.endswith(("due_at", "due_from", "due_to")) and expected is not None:
            try:
                equal = datetime.fromisoformat(actual) == datetime.fromisoformat(expected)
            except (ValueError, TypeError):
                equal = False
        else:
            # Tildes y palabras no se eliminan para no ocultar errores.
            normalize = lambda v: " ".join(v.casefold().split()) if isinstance(v, str) else v
            equal = normalize(actual) == normalize(expected)
        comparisons.append({"campo": path, "esperado": expected,
                            "obtenido": actual, "correcto": resultado is not None and equal})
    return comparisons


def evaluar(filas: list[dict], precio_input: float | None, precio_output: float | None) -> dict:
    validas = [fila for fila in filas if fila["text"].strip()]
    if not validas:
        raise ValueError("No hay mensajes no vacíos para evaluar.")
    llm = GeminiLLM.from_env()
    aciertos = 0
    matriz: Counter = Counter()
    fallos: list[dict] = []
    tiempos: list[float] = []
    tokens_entrada = 0
    tokens_salida = 0
    casos = []
    tiempos_intentos = []
    uso_completo = True

    try:
        for fila in validas:
            time.sleep(PAUSA_ENTRE_LLAMADAS)
            request = IncomingRequest(
                user_id="u-eval", text=fila["text"], channel=Channel.TELEGRAM
            )
            inicio = time.perf_counter()
            try:
                resultado = llm.interpret(request, AHORA)
            except Exception as error:  # noqa: BLE001 - el fallo se contabiliza
                elapsed = (time.perf_counter() - inicio) * 1000
                tiempos_intentos.append(elapsed)
                uso_completo = False
                matriz[(fila["intent"], f"error:{type(error).__name__}")] += 1
                fallos.append(
                    {"id": fila["id"], "esperado": fila["intent"], "error": type(error).__name__}
                )
                casos.append({"id": fila["id"], "error": type(error).__name__,
                              "latencia_ms": elapsed, "campos": comparar_campos(fila, None)})
                continue
            elapsed = (time.perf_counter() - inicio) * 1000
            tiempos.append(elapsed)
            tiempos_intentos.append(elapsed)
            casos.append({"id": fila["id"], "latencia_ms": elapsed,
                          "intencion_correcta": resultado.intent.value == fila["intent"],
                          "campos": comparar_campos(fila, resultado)})

            uso = llm.last_usage()
            if uso is not None:
                tokens_entrada += uso.prompt_tokens
                tokens_salida += uso.candidates_tokens
            else:
                uso_completo = False

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

    finally:
        llm.close()
    p95 = sorted(tiempos_intentos)[math.ceil(len(tiempos_intentos) * 0.95) - 1]
    costo = None
    if precio_input is not None and precio_output is not None:
        costo = (tokens_entrada / 1e6 * precio_input) + (tokens_salida / 1e6 * precio_output)
    campos = [campo for caso in casos for campo in caso["campos"]]
    correctos = sum(c["correcto"] for c in campos)
    exactitud_campos = correctos / len(campos) if campos else None

    return {
        "alcance": "adaptador LLM; sin confirmación, persistencia ni canal",
        "excluidos": [{"id": f["id"], "motivo": "texto vacío; no llega al modelo"}
                      for f in filas if not f["text"].strip()],
        "casos": casos,
        "S1_campos": {
            "esperados": len(campos), "correctos": correctos,
            "exactitud": exactitud_campos, "umbral": 0.90,
            "supera_umbral_extraccion": exactitud_campos >= 0.90 if campos else None,
            "mensajes_evaluados": len(validas), "mensajes_requeridos": 100,
            "cumple_escenario": None,
            "motivo": "S1 exige campos registrados en PostgreSQL en 100 mensajes representativos; este arnés solo mide extracción.",
        },
        "S1_exactitud_intencion": round(aciertos / len(validas), 4),
        "S1_matriz_de_confusion": {
            "{}->{}".format(a, b): n for (a, b), n in sorted(matriz.items())
        },
        "S1_por_intencion": _por_intencion(matriz, len(validas)),
        "S1_fallos": fallos,
        "S3_latencia_ms": {
            "muestras": len(tiempos_intentos),
            "errores": len(validas) - len(tiempos),
            "p50": round(statistics.median(tiempos_intentos), 1),
            "p95": round(p95, 1),
            "maximo": round(max(tiempos_intentos), 1),
            "metodo": "rango más próximo, todos los intentos incluidos",
            "umbral_ms": 7000,
            "dentro_presupuesto_llamada": p95 <= 7000,
            "cumple_escenario": None,
            "motivo": "No mide backend hasta envío al canal.",
        },
        "S5_tokens": {
            "prompt": tokens_entrada,
            "candidates": tokens_salida,
            "costo_usd": round(costo, 6) if costo is not None else None,
            "cobertura_tokens_completa": uso_completo,
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
    parser.add_argument("--precio-input", type=float)
    parser.add_argument("--precio-output", type=float)
    args = parser.parse_args()
    if any(p is not None and (not math.isfinite(p) or p < 0)
           for p in (args.precio_input, args.precio_output)):
        parser.error("Los precios deben ser finitos y no negativos.")
    if (args.precio_input is None) != (args.precio_output is None):
        parser.error("Indique ambos precios o ninguno; omitirlos significa costo desconocido.")
    if args.json and Path(args.json).exists():
        parser.error("La salida ya existe. Use otra ruta para preservar la evidencia anterior.")

    filas = cargar_dataset()
    integridad = validar(filas)

    if args.dry_run:
        print(json.dumps({"integridad": integridad, "estado": "dataset valido"}, ensure_ascii=False, indent=2))
        return 0

    load_dotenv(ROOT / "backend" / ".env")

    if not os.getenv("GEMINI_API_KEY"):
        print(
            "S1 y S3 quedan PENDIENTES: no hay GEMINI_API_KEY.\n"
            "Este guion no inventa mediciones. Defina la clave y vuelva a "
            "ejecutarlo, o use --dry-run para validar el dataset."
        )
        print(json.dumps({"integridad": integridad}, ensure_ascii=False, indent=2))
        return 2

    resultado = {"integridad": integridad}
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    resultado["procedencia"] = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "commit_base": git("rev-parse", "HEAD"),
        "arbol_modificado": bool(git("status", "--porcelain")),
        "dataset_sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(),
        "arnes_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "modelo": os.getenv("GEMINI_MODEL") or _DEFAULT_MODEL,
        "reloj_interpretacion": AHORA.isoformat(),
    }
    resultado.update(evaluar(filas, args.precio_input, args.precio_output))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.json:
        Path(args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))
    return 1 if resultado["S3_latencia_ms"]["errores"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
