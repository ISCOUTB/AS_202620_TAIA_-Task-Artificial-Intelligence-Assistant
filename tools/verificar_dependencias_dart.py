"""Verificacion reproducible de las dependencias del cliente Flutter.

Uso:
    python tools/verificar_dependencias_dart.py
    python tools/verificar_dependencias_dart.py --online
    python tools/verificar_dependencias_dart.py --json docs/verificacion_dependencias_dart.json

Comprueba, sin red salvo que se pase ``--online``:

  * que cada paquete de ``frontend/pubspec.lock`` tenga version y origen;
  * que los paquetes alojados en pub.dev tengan ``sha256`` y la URL oficial;
  * que no haya dependencias ``git`` ni ``path``, que traerian codigo sin revisar;
  * que cada dependencia directa de ``pubspec.yaml`` aparezca en el lock con el
    tipo correcto (``direct main`` o ``direct dev``).

Con ``--online`` consulta OSV (ecosistema ``Pub``), igual que pip-audit hace con
Python. Sin ese flag no se hace ninguna peticion de red.

Limite conocido: se verifica que la restriccion de ``pubspec.yaml`` este
declarada, no que la version resuelta la satisfaga; eso lo garantiza ``pub get``.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "frontend" / "pubspec.lock"
PUBSPEC = ROOT / "frontend" / "pubspec.yaml"

URL_OFICIAL = "https://pub.dev"
OSV_URL = "https://api.osv.dev/v1/querybatch"

PATRON_SHA256 = re.compile(r"^[0-9a-f]{64}$")
TIPOS_DEPENDENCIA = ("direct main", "direct dev", "transitive")
ORIGENES_PERMITIDOS = ("hosted", "sdk")


def _limpiar(valor: str) -> str:
    """Quita comillas y comentarios de un valor escalar de YAML."""

    limpio = valor.split(" #", 1)[0].strip()
    if len(limpio) >= 2 and limpio[0] == limpio[-1] and limpio[0] in "\"'":
        limpio = limpio[1:-1]
    return limpio


def analizar_lock(texto: str) -> dict[str, dict]:
    """Extrae los paquetes del lock. El formato de pub es estable y plano."""

    paquetes: dict[str, dict] = {}
    actual: str | None = None
    bloque: str | None = None

    for linea in texto.splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        sangria = len(linea) - len(linea.lstrip())
        contenido = linea.strip()

        if sangria == 0:
            bloque = contenido.rstrip(":")
            actual = None
            continue
        if bloque != "packages":
            continue
        if sangria == 2 and contenido.endswith(":"):
            actual = contenido[:-1].strip()
            paquetes[actual] = {
                "nombre": actual,
                "dependency": None,
                "source": None,
                "version": None,
                "sha256": None,
                "url": None,
            }
            continue
        if actual is None:
            continue

        clave, _, valor = contenido.partition(":")
        valor = _limpiar(valor)
        if sangria == 4:
            paquetes[actual][clave.strip()] = valor or None
        elif sangria == 6:
            paquetes[actual][clave.strip()] = valor or None

    return paquetes


def analizar_pubspec(texto: str) -> dict[str, list[str]]:
    """Devuelve las dependencias directas declaradas, incluidas las del SDK."""

    directas: dict[str, list[str]] = {"main": [], "dev": []}
    seccion: str | None = None

    for linea in texto.splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        limpia = linea.split(" #", 1)[0].rstrip()
        if not linea.startswith(" ") and limpia.endswith(":"):
            seccion = limpia[:-1].strip()
            continue
        if seccion not in ("dependencies", "dev_dependencies"):
            continue
        if not linea.startswith("  ") or linea.startswith("    "):
            continue

        nombre, _, _restriccion = limpia.strip().partition(":")
        # "flutter:" y "flutter_test:" usan un bloque sdk; se registran igual
        # porque el lock las marca como directas.
        clave = "main" if seccion == "dependencies" else "dev"
        directas[clave].append(nombre.strip())

    return directas


def analizar_sdks(texto: str) -> dict[str, str]:
    """Lee el bloque `sdks` del lock: la version minima de Dart y de Flutter."""

    sdks: dict[str, str] = {}
    bloque: str | None = None

    for linea in texto.splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        sangria = len(linea) - len(linea.lstrip())
        contenido = linea.strip()
        if sangria == 0:
            bloque = contenido.rstrip(":")
            continue
        if bloque != "sdks" or sangria != 2:
            continue
        clave, _, valor = contenido.partition(":")
        sdks[clave.strip()] = _limpiar(valor)

    return sdks


def version_minima_pubspec(texto: str) -> str | None:
    """Extrae la version minima de `environment.sdk` en pubspec.yaml."""

    seccion: str | None = None
    for linea in texto.splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        limpia = linea.split(" #", 1)[0].rstrip()
        if not linea.startswith(" ") and limpia.endswith(":"):
            seccion = limpia[:-1].strip()
            continue
        if seccion != "environment":
            continue
        if not linea.startswith("  ") or linea.startswith("    "):
            continue
        clave, _, valor = limpia.strip().partition(":")
        if clave.strip() == "sdk":
            minimo = re.search(r"\d+\.\d+\.\d+", valor)
            return minimo.group(0) if minimo else None
    return None


def _problemas_del_lock(paquetes: dict[str, dict]) -> tuple[list[str], list[str], list[str], list[str]]:
    sin_version: list[str] = []
    sin_sha256: list[str] = []
    origenes_no_permitidos: list[str] = []
    problemas: list[str] = []

    for nombre, paquete in sorted(paquetes.items()):
        if not paquete.get("version"):
            sin_version.append(nombre)
            problemas.append("{}: sin version en el lock".format(nombre))

        origen = paquete.get("source") or ""
        if not origen:
            problemas.append("{}: sin origen en el lock".format(nombre))
        elif origen not in ORIGENES_PERMITIDOS:
            origenes_no_permitidos.append("{} ({})".format(nombre, origen))
            problemas.append("{}: origen no permitido '{}'".format(nombre, origen))

        tipo = paquete.get("dependency") or ""
        if tipo not in TIPOS_DEPENDENCIA:
            problemas.append("{}: tipo de dependencia desconocido '{}'".format(nombre, tipo))

        if origen == "hosted":
            sha = paquete.get("sha256") or ""
            if not PATRON_SHA256.match(sha):
                sin_sha256.append(nombre)
                problemas.append("{}: sin sha256 valido en el lock".format(nombre))
            if paquete.get("url") != URL_OFICIAL:
                problemas.append(
                    "{}: el origen alojado no es {} ('{}')".format(nombre, URL_OFICIAL, paquete.get("url"))
                )

    return sin_version, sin_sha256, origenes_no_permitidos, problemas


def _problemas_de_directas(paquetes: dict[str, dict], directas: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    faltantes: list[str] = []
    problemas: list[str] = []

    for clave, esperado in (("main", "direct main"), ("dev", "direct dev")):
        for nombre in directas[clave]:
            paquete = paquetes.get(nombre)
            if paquete is None:
                faltantes.append(nombre)
                problemas.append("{}: dependencia directa declarada pero ausente del lock".format(nombre))
                continue
            if paquete.get("dependency") != esperado:
                problemas.append(
                    "{}: el lock la marca como '{}' y pubspec.yaml la declara como '{}'".format(
                        nombre, paquete.get("dependency"), esperado
                    )
                )

    declaradas = set(directas["main"]) | set(directas["dev"])
    for nombre, paquete in sorted(paquetes.items()):
        if paquete.get("dependency", "").startswith("direct") and nombre not in declaradas:
            problemas.append(
                "{}: el lock la marca como directa pero pubspec.yaml no la declara".format(nombre)
            )

    return faltantes, problemas


def consultar_osv(paquetes: dict[str, dict], transporte=None) -> list[dict]:
    """Consulta OSV por lote. ``transporte`` permite inyectar uno falso en tests."""

    consultas = [
        {"package": {"name": paquete["nombre"], "ecosystem": "Pub"}, "version": paquete["version"]}
        for paquete in paquetes.values()
        if paquete.get("source") == "hosted" and paquete.get("version")
    ]
    if not consultas:
        return []

    cuerpo = json.dumps({"queries": consultas}).encode("utf-8")
    if transporte is None:
        peticion = urllib.request.Request(
            OSV_URL, data=cuerpo, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:  # noqa: S310 - URL fija https
            datos = json.loads(respuesta.read().decode("utf-8"))
    else:
        datos = transporte(cuerpo)

    hallazgos: list[dict] = []
    for consulta, resultado in zip(consultas, datos.get("results", [])):
        for vulnerabilidad in resultado.get("vulns", []):
            hallazgos.append(
                {
                    "paquete": consulta["package"]["name"],
                    "version": consulta["version"],
                    "id": vulnerabilidad.get("id"),
                    "resumen": vulnerabilidad.get("summary", ""),
                    "alias": vulnerabilidad.get("aliases", []),
                }
            )
    return hallazgos


def _normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower().strip()


def analizar(
    lock_texto: str,
    pubspec_texto: str,
    transporte=None,
    online: bool = False,
) -> dict:
    """Devuelve el resultado completo, con o sin la consulta a OSV."""

    paquetes = analizar_lock(lock_texto)
    directas = analizar_pubspec(pubspec_texto)

    sin_version, sin_sha256, origenes_no_permitidos, problemas = _problemas_del_lock(paquetes)
    faltantes, problemas_directas = _problemas_de_directas(paquetes, directas)
    problemas.extend(problemas_directas)

    sdks = analizar_sdks(lock_texto)
    minimo = version_minima_pubspec(pubspec_texto)
    if not sdks.get("dart"):
        problemas.append("el lock no declara la version minima de Dart en 'sdks'")
    elif minimo and minimo not in sdks["dart"]:
        problemas.append(
            "pubspec.yaml exige Dart {} y el lock declara '{}'".format(minimo, sdks["dart"])
        )

    vulnerabilidades: list[dict] = []
    if online:
        try:
            vulnerabilidades = consultar_osv(paquetes, transporte=transporte)
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            problemas.append("no se pudo consultar OSV: {}".format(error))
        for hallazgo in vulnerabilidades:
            problemas.append(
                "{} {}: {} {}".format(
                    hallazgo["paquete"], hallazgo["version"], hallazgo["id"], hallazgo["resumen"]
                ).strip()
            )

    por_dependencia: dict[str, int] = {}
    por_origen: dict[str, int] = {}
    for paquete in paquetes.values():
        tipo = paquete.get("dependency") or "desconocido"
        origen = paquete.get("source") or "desconocido"
        por_dependencia[tipo] = por_dependencia.get(tipo, 0) + 1
        por_origen[origen] = por_origen.get(origen, 0) + 1

    return {
        "lock": str(LOCK.relative_to(ROOT)).replace("\\", "/"),
        "paquetes": len(paquetes),
        "por_dependencia": dict(sorted(por_dependencia.items())),
        "por_origen": dict(sorted(por_origen.items())),
        "directas_declaradas": {"main": sorted(directas["main"]), "dev": sorted(directas["dev"])},
        "sin_version": sin_version,
        "sin_sha256": sin_sha256,
        "origenes_no_permitidos": origenes_no_permitidos,
        "directas_faltantes": faltantes,
        "sdks": sdks,
        "osv_consultado": online,
        "vulnerabilidades": vulnerabilidades,
        "problemas": problemas,
        "veredicto": "ok" if not problemas else "con problemas",
    }


def _ruta_en_repositorio(parser: argparse.ArgumentParser, valor: str) -> Path:
    ruta = Path(valor).resolve()
    if not ruta.is_relative_to(ROOT):
        parser.error("La ruta debe estar dentro del repositorio: {}".format(valor))
    return ruta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Consulta OSV por CVE en el ecosistema Pub.")
    parser.add_argument("--json", help="Ruta opcional para volcar el resultado.")
    args = parser.parse_args()

    for ruta in (LOCK, PUBSPEC):
        if not ruta.is_file():
            parser.error("No existe: {}".format(ruta.relative_to(ROOT)))

    resultado = analizar(
        LOCK.read_text(encoding="utf-8"),
        PUBSPEC.read_text(encoding="utf-8"),
        online=args.online,
    )

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.json:
        _ruta_en_repositorio(parser, args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))

    return 0 if resultado["veredicto"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
