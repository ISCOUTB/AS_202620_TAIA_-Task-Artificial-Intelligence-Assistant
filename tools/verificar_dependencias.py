"""Verificacion reproducible de las dependencias y de credenciales (bloque D).

Uso:
    python tools/verificar_dependencias.py
    python tools/verificar_dependencias.py --json salida.json

Comprueba, sin red:

  * que todo paquete de los lock files tenga version fijada con ``==``;
  * que todo paquete tenga al menos un hash ``--hash=sha256:``;
  * que las dependencias exclusivas de Windows esten presentes, porque los
    locks se generaron en Linux y sin ellas la instalacion falla en Windows;
  * que el arbol versionado no contenga credenciales con formato de producción.

Las consultas a PyPI no se hacen aqui: los hashes se comparan contra el lock,
que es lo que ``pip --require-hashes`` enforcementa al instalar.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOCKS = {
    "produccion": ROOT / "backend" / "requirements.lock.txt",
    "desarrollo": ROOT / "backend" / "requirements-dev.lock.txt",
}

# Dependencias que solo se instalan en Windows y que un lock generado en Linux
# omite. Sin ellas, `pip install --require-hashes` aborta en Windows.
ESPECIFICAS_DE_WINDOWS = {
    "tzdata": "sys_platform == \"win32\"",
    "colorama": "sys_platform == \"win32\"",
}

# Solo se busca en archivos versionados, y solo patrones de produccion. Los
# literales se componen por trozos para que este archivo no coincida consigo
# mismo, y el propio archivo queda excluido del escaneo.
_PAT_GEMINI = "AI" + "za" + r"[0-9A-Za-z_\-]{35}"
_PAT_POOLER = r"pooler" + r"\." + "supabase" + r"\." + "com"

PATRONES_CREDENCIAL = {
    "api key de Gemini": re.compile(_PAT_GEMINI),
    "URL de pooler de Supabase": re.compile(_PAT_POOLER),
    "credencial de OCI": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    "token de GitHub": re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}"),
    "jwt en un archivo": re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\."),
}

ESTE_ARCHIVO = "tools/verificar_dependencias.py"

RUTAS_EXCLUIDAS = {
    ".venv",
    "node_modules",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".terraform",
}


def _versionada(relativo: str) -> bool:
    return not any(parte in RUTAS_EXCLUIDAS for parte in Path(relativo).parts)


def analizar_lock(ruta: Path) -> dict:
    """Extrae los paquetes declarados y sus hashes."""

    texto = ruta.read_text(encoding="utf-8")
    # Une las lineas_logica para capturar los paquetes con continuacion "\".
    logicas: list[str] = []
    buffer = ""
    for linea in texto.splitlines():
        if linea.rstrip().endswith("\\"):
            buffer += linea.rstrip()[:-1]
            continue
        logicas.append(buffer + linea)
        buffer = ""
    if buffer:
        logicas.append(buffer)

    paquetes: dict[str, dict] = {}
    for logica in logicas:
        limpia = logica.strip()
        if not limpia or limpia.startswith("#"):
            continue
        if limpia.startswith("-r ") or limpia.startswith("--"):
            continue
        empareja = re.match(r"^([A-Za-z0-9._\-]+)\s*==\s*([^\s;\\]+)", limpia)
        nombre = empareja.group(1) if empareja else limpia.split()[0]
        entrada = paquetes.setdefault(
            nombre,
            {"nombre": nombre, "version": None, "hashes": 0, "marcador": None},
        )
        if empareja:
            entrada["version"] = empareja.group(2)
        entrada["hashes"] += len(re.findall(r"--hash=sha256:[0-9a-f]{64}", limpia))
        if ";" in limpia:
            entrada["marcador"] = limpia.split(";", 1)[1].strip()

    sin_version = sorted(n for n, p in paquetes.items() if p["version"] is None)
    sin_hash = sorted(n for n, p in paquetes.items() if p["hashes"] == 0)
    return {
        "archivo": str(ruta.relative_to(ROOT)).replace("\\", "/"),
        "paquetes": len(paquetes),
        "sin_version_fijada": sin_version,
        "sin_hash": sin_hash,
        "detalle": {n: p for n, p in sorted(paquetes.items())},
    }


def buscar_credenciales() -> list[dict]:
    """Escanea los archivos versionados buscando credenciales de produccion."""

    salida = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=ROOT
    ).stdout.splitlines()
    hallazgos: list[dict] = []
    for relativo in salida:
        if not relativo or not _versionada(relativo):
            continue
        if relativo.replace("\\", "/") == ESTE_ARCHIVO:
            continue
        ruta = ROOT / relativo
        if not ruta.is_file():
            continue
        try:
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for nombre, patron in PATRONES_CREDENCIAL.items():
            for coincidencia in patron.finditer(texto):
                hallazgos.append(
                    {
                        "archivo": relativo.replace("\\", "/"),
                        "tipo": nombre,
                        "linea": texto[: coincidencia.start()].count("\n") + 1,
                    }
                )
    return hallazgos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="Ruta opcional para volcar el resultado.")
    args = parser.parse_args()

    locks = {nombre: analizar_lock(ruta) for nombre, ruta in LOCKS.items()}

    faltan_windows: list[str] = []
    for especificas in ESPECIFICAS_DE_WINDOWS:
        if especificas not in locks["desarrollo"]["detalle"]:
            faltan_windows.append(especificas)

    credenciales = buscar_credenciales()

    problemas = 0
    for nombre, lock in locks.items():
        problemas += len(lock["sin_version_fijada"]) + len(lock["sin_hash"])
    problemas += len(faltan_windows) + len(credenciales)

    resultado = {
        "locks": locks,
        "windows_dependencias_requeridas": sorted(ESPECIFICAS_DE_WINDOWS),
        "windows_dependencias_faltantes": faltan_windows,
        "credenciales_en_arbol_versionado": credenciales,
        "problemas": problemas,
        "veredicto": "ok" if problemas == 0 else "con problemas",
    }

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.json:
        Path(args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))

    return 0 if problemas == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())