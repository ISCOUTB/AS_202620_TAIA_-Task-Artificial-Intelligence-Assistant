"""Evaluacion offline de la confirmacion de escrituras (S1, S2 y S5).

Uso:
    python tools/eval_confirmacion.py [--json salida.json]

Mide tres cosas sobre la porcion determinista del asistente: la confirmacion
de una escritura. No llama a Gemini ni a la red, asi que NO mide S1 de
interpretacion de intencion ni S3 de latencia de extremo a extremo. Mide:

  * exactitud de confirmacion: formas de "si" que el estudiante puede escribir
    y que el asistente debe entender como confirmacion;
  * escrituras indebidas: respuestas que NO son confirmacion y que aun asi
    crean la tarea;
  * latencia de la confirmacion, sin red (p50 y p95).

El guion usa el caso de uso real con los dobles de prueba del modulo AI, no una
reimplementacion de la normalizacion.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.ai.adapters.outbound.fake_llm import FakeLLM  # noqa: E402
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import (  # noqa: E402
    InMemoryAcademicGateway,
)
from app.modules.ai.adapters.outbound.in_memory_conversation_store import (  # noqa: E402
    InMemoryConversationStore,
)
from app.modules.ai.application.dto import TaskFilters  # noqa: E402
from app.modules.ai.application.use_cases.handle_message import (  # noqa: E402
    HandleUserMessageUseCase,
)
from app.modules.ai.domain.messages import (  # noqa: E402
    Channel,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
)

TZ = timezone(timedelta(hours=-5))
DUE = datetime(2026, 9, 20, 20, 0, tzinfo=TZ)
AHORA = datetime(2026, 9, 10, 12, 0, tzinfo=TZ)

# Palabras afirmativas que el caso de uso reconoce como confirmacion.
AFIRMATIVAS = ["si", "sí", "s", "dale", "ok", "confirmo", "yes", "listo", "hazlo"]

# Envolturas ortograficas que un estudiante produce al escribir en un movil.
ENVOLTURAS = [
    "{}",
    "{}. ",
    "{}!",
    "{}?",
    "{}...",
    "{}…",
    ", {},",
    "  {}  ",
    "\t{}",
    "¡{}!",
    "¿{}?",
    "«{}»",
    "{} ;",
    "( {}) ",
]

# Respuestas que NO son confirmacion. Las primeras son negativas explicitas y
# las restantes se parecen a una confirmacion para medir escrituras indebidas.
NEGATIVAS = [
    "no",
    "n",
    "cancela",
    "cancelar",
    "nop",
    "nope",
    "nooo",
    "nel",
    "no sé",
    "ahora no",
    "no!no",
    "sí no",
    "más tarde",
    "todavía no",
    "después",
    "quizás",
    "sii",
    "siii",
    "no confirmo",
    "crea la tarea del taller",
]


def _variantes() -> list[str]:
    """Todas las combinaciones de palabra, capitalizacion y envoltura."""

    vistas: set[str] = set()
    for palabra in AFIRMATIVAS:
        for forma in (palabra, palabra.capitalize(), palabra.upper()):
            for envoltura in ENVOLTURAS:
                vistas.add(envoltura.format(forma))
    return sorted(vistas)


def _caso() -> tuple[HandleUserMessageUseCase, InMemoryAcademicGateway]:
    academic = InMemoryAcademicGateway()
    caso = HandleUserMessageUseCase(
        llm=FakeLLM(
            [
                Interpretation(
                    Intent.CREATE_TASK,
                    0.9,
                    task=ExtractedTaskData(title="Taller", due_at=DUE),
                )
            ]
        ),
        academic=academic,
        conversations=InMemoryConversationStore(),
        now=lambda: AHORA,
    )
    caso.execute(
        IncomingRequest(
            user_id="u1", text="crea la tarea taller", channel=Channel.TELEGRAM
        )
    )
    return caso, academic


def _confirmar(respuesta: str) -> tuple[bool, float]:
    """Ejecuta la confirmacion y devuelve (creo_tarea, milisegundos)."""

    caso, academic = _caso()
    inicio = time.perf_counter()
    caso.execute(
        IncomingRequest(user_id="u1", text=respuesta, channel=Channel.TELEGRAM)
    )
    transcurrido = (time.perf_counter() - inicio) * 1000
    creada = len(academic.list_tasks("u1", TaskFilters())) == 1
    return creada, transcurrido


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="Ruta opcional para volcar el resultado.")
    args = parser.parse_args()

    afirmativas = _variantes()
    aceptadas: list[str] = []
    rechazadas_por_falso: list[str] = []
    tiempos: list[float] = []

    for respuesta in afirmativas:
        creada, ms = _confirmar(respuesta)
        tiempos.append(ms)
        (aceptadas if creada else rechazadas_por_falso).append(respuesta)

    escrituras_indebidas: list[str] = []
    for respuesta in NEGATIVAS:
        creada, ms = _confirmar(respuesta)
        tiempos.append(ms)
        if creada:
            escrituras_indebidas.append(respuesta)

    percentiles = statistics.quantiles(tiempos, n=100) if len(tiempos) > 1 else [0.0]

    resultado = {
        "alcance": "confirmacion de escrituras, sin red y sin Gemini",
        "no_mide": [
            "S1 interpretacion de intencion del modelo de lenguaje",
            "S3 latencia de extremo a extremo",
        ],
        "afirmativas": {
            "total": len(afirmativas),
            "aceptadas": len(aceptadas),
            "exactitud": round(len(aceptadas) / len(afirmativas), 4),
            "rechazadas_indebidamente": rechazadas_por_falso,
        },
        "negativas": {
            "total": len(NEGATIVAS),
            "escrituras_indebidas": escrituras_indebidas,
            "tasa_escritura_indebida": round(len(escrituras_indebidas) / len(NEGATIVAS), 4),
        },
        "latencia_confirmacion_ms": {
            "muestras": len(tiempos),
            "p50": round(statistics.median(tiempos), 4),
            "p95": round(percentiles[94], 4),
            "maximo": round(max(tiempos), 4),
        },
    }

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.json:
        Path(args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))

    return 0 if not rechazadas_por_falso and not escrituras_indebidas else 1


if __name__ == "__main__":
    raise SystemExit(main())