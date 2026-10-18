"""Auditoria mecanica de erosion de contexto y propiedad de datos (S6/S8).

Uso:
    python tools/audit_boundaries.py
    python tools/audit_boundaries.py --json salida.json

No requiere red ni base de datos. Analiza el arbol de modulos con ``ast`` y
comprueba dos cosas distintas que se confunden a menudo:

  * que ningun adaptador de entrada componga sus propias dependencias de
    salida (la composicion concreta pertenece al composition root, ``main.py``);
  * que las fronteras de V-01 a V-03 sigan cerradas, es decir, que ningun
    contexto alcance los adaptadores HTTP, repositorios o entidades internas de
    otro contexto.

Consultar un dato de otro contexto por un contrato no es una violacion. Instalar
un repositorio concreto desde el adaptador HTTP si lo es, porque el transporte
pasa a decidir que implementacion se usa y cuando se construye.

Sale con codigo distinto de cero si encuentra alguna infraccion.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "backend" / "app" / "modules"

# Nombres que delatan acceso directo a la persistencia de otro adaptador.
PERSISTENCIA = ("Repository", "repository", "Store", "store", "Session", "session")

# Contextos whose concrete composition must live in main.py.
CONTEXTOS = sorted(p.name for p in MODULES.iterdir() if p.is_dir() and not p.name.startswith("_"))

# Objetos de FastAPI que viven a nivel de modulo sin ser dependencias: son
# declaraciones de ruta o de seguridad, no colaboradores del caso de uso.
EXCLUIDOS_R4 = {"HTTPBearer", "HTTPAuthorizationCredentials", "OAuth2PasswordBearer", "APIRouter"}


def _entrantes() -> list[Path]:
    return sorted(
        ruta
        for contexto in MODULES.iterdir()
        if contexto.is_dir()
        for entrada in (contexto / "adapters" / "inbound").rglob("*.py")
        for ruta in [entrada]
    )


def _modulo_de(ruta: Path) -> str:
    return ".".join(ruta.relative_to(ROOT / "backend").with_suffix("").parts)


def _hallazgo(regla: str, ruta: Path, linea: int, detalle: str) -> dict:
    return {
        "regla": regla,
        "archivo": str(ruta.relative_to(ROOT)).replace("\\", "/"),
        "linea": linea,
        "detalle": detalle,
    }


def _composicion_en_llamada(nodo: ast.Call) -> list[tuple[str, str]]:
    """R3 y R1 sobre una llamada: lectura del entorno o proveedor de persistencia."""

    encontrados: list[tuple[str, str]] = []
    # R3: la configuracion del proveedor se lee en el transporte.
    if isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "from_env":
        encontrados.append((
            "R3",
            "el adaptador de entrada construye el adaptador de salida "
            "leyendo el entorno ({}).from_env()".format(nodo.func.attr),
        ))
    if isinstance(nodo.func, ast.Name):
        if nodo.func.id in {"getenv", "environ"}:
            encontrados.append(("R3", "el adaptador de entrada lee el entorno"))
        # R1: el adaptador de entrada instala una persistencia concreta.
        if nodo.func.id.startswith("get_") and nodo.func.id.endswith(
            ("repository", "provider", "sender")
        ):
            encontrados.append((
                "R1",
                "{}(): proveedor de persistencia propio invocado desde el "
                "transporte".format(nodo.func.id),
            ))
    return encontrados


def _persistencia_propia(nodo: ast.ImportFrom, contexto: str) -> str | None:
    """R2: import directo de la persistencia concreta del contexto."""

    if not nodo.module:
        return None
    partes = nodo.module.split(".")
    es_propio = (
        len(partes) >= 4
        and partes[2] == "adapters"
        and partes[3] == "outbound"
        and partes[1] == contexto
    )
    if es_propio and any(
        any(p.name.startswith(prefijo) for prefijo in PERSISTENCIA)
        for p in nodo.names
    ):
        importado = ", ".join(p.name for p in nodo.names)
        return "el adaptador de entrada importa la persistencia concreta propia: {}".format(importado)
    return None


def _singletons(nodo: ast.Assign) -> list[str]:
    """R4: singleton construido al importar el modulo.

    Se excluyen los objetos de infraestructura de FastAPI (HTTPBearer,
    APIRouter), que son objetos de declaracion de ruta y no dependencias.
    """

    if nodo.col_offset != 0 or not isinstance(nodo.value, ast.Call):
        return []
    denoted = getattr(nodo.value.func, "id", "")
    denoted = denoted or getattr(nodo.value.func, "attr", "")
    if denoted in EXCLUIDOS_R4:
        return []
    return [
        "{} = {}() se construye al importar el modulo".format(objetivo.id, denoted)
        for objetivo in nodo.targets
        if isinstance(objetivo, ast.Name) and objetivo.id.startswith("_")
    ]


def _auditar_entrante(ruta: Path) -> list[dict]:
    """R1..R4: composicion dentro del adaptador de entrada."""

    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    contexto = ruta.relative_to(MODULES).parts[0]
    hallazgos: list[dict] = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            for regla, detalle in _composicion_en_llamada(nodo):
                hallazgos.append(_hallazgo(regla, ruta, nodo.lineno, detalle))

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            detalle = _persistencia_propia(nodo, contexto)
            if detalle:
                hallazgos.append(_hallazgo("R2", ruta, nodo.lineno, detalle))
        if isinstance(nodo, ast.Assign):
            for detalle in _singletons(nodo):
                hallazgos.append(_hallazgo("R4", ruta, nodo.lineno, detalle))

    return hallazgos


# -- V-01..V-03: las fronteras anteriores siguen cerradas -------------------
REQUISITOS_FRONTERA = {
    "V-01": "ningun contexto debe importar el adaptador HTTP de Usuario",
    "V-02": "AI ni Reminders deben alcanzar el proveedor de repositorios de Academic",
    "V-03": "AI no debe importar la entidad de dominio Task de Academic",
}
PATRONES_FRONTERA = {
    "V-01": "usuario.adapters.inbound",
    "V-02": "academic.adapters.outbound.repository_provider",
    "V-03": "academic.domain.entities",
}
# Contexto propietario de cada frontera: puede usar su propio codigo.
PROPIETARIO_FRONTERA = {"V-01": "usuario", "V-02": "academic", "V-03": "academic"}


def _infracciones_de_frontera(clave: str) -> list[str]:
    infracciones: list[str] = []
    # Se recorre solo MODULES: `backend/app/main.py` es el composition root
    # y por definicion puede componer las implementaciones concretas.
    for archivo in MODULES.rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        if PATRONES_FRONTERA[clave] not in texto:
            continue
        if archivo.relative_to(MODULES).parts[0] == PROPIETARIO_FRONTERA[clave]:
            continue
        infracciones.append(str(archivo.relative_to(ROOT)).replace("\\", "/"))
    return infracciones


def auditar() -> dict:
    hallazgos: list[dict] = []
    for ruta in _entrantes():
        hallazgos.extend(_auditar_entrante(ruta))

    cerradas: dict[str, list[str]] = {}
    for clave in PATRONES_FRONTERA:
        infracciones = _infracciones_de_frontera(clave)
        cerradas[clave] = infracciones
        if infracciones:
            hallazgos.append(_hallazgo(
                clave,
                ROOT / infracciones[0],
                0,
                "{} ({} apariciones)".format(REQUISITOS_FRONTERA[clave], len(infracciones)),
            ))

    return {
        "contextos": CONTEXTOS,
        "adaptadores_de_entrada_analizados": len(_entrantes()),
        "fronteras_anteriores": cerradas,
        "infracciones": hallazgos,
        "infracciones_totales": len(hallazgos),
    }


def _clave(hallazgo: dict) -> str:
    """Identidad estable de un hallazgo, para compararlo con la linea base."""

    return "{}|{}".format(hallazgo["regla"], hallazgo["archivo"])


def _ruta_en_repositorio(parser: argparse.ArgumentParser, valor: str) -> Path:
    """Acepta solo rutas dentro del repositorio para leer o escribir evidencia."""

    ruta = Path(valor).resolve()
    if not ruta.is_relative_to(ROOT):
        parser.error("La ruta debe estar dentro del repositorio: {}".format(valor))
    return ruta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="Ruta opcional para volcar el resultado.")
    parser.add_argument(
        "--baseline",
        default=str(ROOT / "docs" / "auditoria_fronteras_baseline.json"),
        help="Hallazgos ya analizados y aceptados, que no cuentan como regresión.",
    )
    parser.add_argument(
        "--escribir-baseline",
        action="store_true",
        help="Regenera el archivo de línea base con los hallazgos actuales.",
    )
    args = parser.parse_args()

    resultado = auditar()
    ruta_base = _ruta_en_repositorio(parser, args.baseline)

    if args.escribir_baseline:
        ruta_base.write_text(
            json.dumps(
                sorted({_clave(h) for h in resultado["infracciones"]}),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print("linea base escrita: {}".format(ruta_base))

    aceptadas: set[str] = set()
    if ruta_base.is_file():
        aceptadas = set(json.loads(ruta_base.read_text(encoding="utf-8")))

    regresiones = [h for h in resultado["infracciones"] if _clave(h) not in aceptadas]
    resultado["linea_base"] = str(ruta_base.relative_to(ROOT)).replace("\\", "/")
    resultado["aceptadas_en_linea_base"] = len(resultado["infracciones"]) - len(regresiones)
    resultado["regresiones"] = regresiones
    resultado["regresiones_totales"] = len(regresiones)

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.json:
        _ruta_en_repositorio(parser, args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))

    return 0 if not regresiones else 1


if __name__ == "__main__":
    raise SystemExit(main())
