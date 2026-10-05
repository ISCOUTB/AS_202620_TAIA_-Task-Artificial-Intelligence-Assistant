"""Captura evidencia reproducible de una corrida de pruebas para la entrega S8.

Uso:
    python tools/evidencia_s8.py baseline
    python tools/evidencia_s8.py pre-fix
    python tools/evidencia_s8.py post-fix

El entorno de pruebas se toma de las variables TEST_DATABASE_URL y DATABASE_URL.
Este script no imprime ni registra contrasenas: solo guarda la salida de pytest,
el resumen y el commit vigente.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = "docs/evidencia_s8_{}.txt"


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=RAIZ
    ).stdout.strip()


def _rama() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=RAIZ,
    ).stdout.strip()


def _entorno() -> list[str]:
    """Describe el entorno sin exponer credenciales."""

    def host(url: str | None) -> str:
        if not url or "@" not in url:
            return "(sin configurar)"
        return url.rsplit("@", 1)[1]

    return [
        "python      : " + sys.version.split()[0],
        "plataforma  : " + sys.platform,
        "rama        : " + _rama(),
        "commit      : " + _commit(),
        "TEST_DATABASE_URL -> " + host(os.getenv("TEST_DATABASE_URL")),
        "DATABASE_URL      -> " + host(os.getenv("DATABASE_URL")),
    ]


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"baseline", "pre-fix", "post-fix"}:
        print(__doc__)
        return 2

    etiqueta = sys.argv[1]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests", "-q"],
        capture_output=True,
        text=True,
        cwd=RAIZ,
    )

    lineas = [
        "=" * 78,
        "EVIDENCIA S8 - {}".format(etiqueta.upper()),
        "=" * 78,
        "generado    : " + datetime.now(timezone.utc).astimezone().isoformat(),
        * _entorno(),
        "",
        "comando     : python -m pytest backend/tests -q",
        "",
        "-" * 78,
        "SALIDA DE PYTEST",
        "-" * 78,
        proc.stdout.strip(),
    ]
    if proc.stderr.strip():
        lineas += ["", proc.stderr.strip()]
    lineas += [
        "",
        "-" * 78,
        "codigo de salida: {}".format(proc.returncode),
        "-" * 78,
        "",
    ]

    destino = RAIZ / SALIDA.format(etiqueta)
    destino.write_text("\n".join(lineas), encoding="utf-8")
    print("escrito: {}".format(destino.relative_to(RAIZ)))
    print("codigo de salida: {}".format(proc.returncode))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())