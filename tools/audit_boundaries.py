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
CONTEXTOS = sorted(p.name for p in MODULES.iterdir() if p.is_dir())

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


def auditar() -> dict:
    hallazgos: list[dict] = []

    def anotar(regla: str, ruta: Path, linea: int, detalle: str) -> None:
        hallazgos.append(
            {
                "regla": regla,
                "archivo": str(ruta.relative_to(ROOT)).replace("\\", "/"),
                "linea": linea,
                "detalle": detalle,
            }
        )

    # -- R1..R4: composicion dentro del adaptador de entrada ----------------
    for ruta in _entrantes():
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        contexto = ruta.relative_to(MODULES).parts[0]

        for nodo in ast.walk(arbol):
            # R3: la configuracion del proveedor se lee en el transporte.
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr == "from_env":
                    anotar(
                        "R3",
                        ruta,
                        nodo.lineno,
                        "el adaptador de entrada construye el adaptador de salida "
                        "leyendo el entorno ({}).from_env()".format(nodo.func.attr),
                    )
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                if nodo.func.id in {"getenv", "environ"}:
                    anotar("R3", ruta, nodo.lineno, "el adaptador de entrada lee el entorno")

            # R1: el adaptador de entrada instala una persistencia concreta.
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                if nodo.func.id.startswith("get_") and nodo.func.id.endswith(
                    ("repository", "provider", "sender")
                ):
                    anotar(
                        "R1",
                        ruta,
                        nodo.lineno,
                        "{}(): proveedor de persistencia propio invocado desde el "
                        "transporte".format(nodo.func.id),
                    )

        for nodo in ast.walk(arbol):
            # R2: import directo de la persistencia concreta del contexto.
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
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
                    anotar(
                        "R2",
                        ruta,
                        nodo.lineno,
                        "el adaptador de entrada importa la persistencia concreta "
                        "propia: {}".format(importado),
                    )

            # R4: singleton construido al importar el modulo. Se excluyen los
            # objetos de infraestructura de FastAPI (HTTPBearer, APIRouter),
            # que son objetos de declaracion de ruta y no dependencias.
            if isinstance(nodo, ast.Assign) and nodo.col_offset == 0:
                for objetivo in nodo.targets:
                    if isinstance(objetivo, ast.Name) and objetivo.id.startswith("_"):
                        if isinstance(nodo.value, ast.Call):
                            denoted = getattr(nodo.value.func, "id", "")
                            denoted = denoted or getattr(nodo.value.func, "attr", "")
                            if denoted in EXCLUIDOS_R4:
                                continue
                            anotar(
                                "R4",
                                ruta,
                                nodo.lineno,
                                "{} = {}() se construye al importar el modulo".format(
                                    objetivo.id, denoted
                                ),
                            )

    # -- V-01..V-03: las fronteras anteriores siguen cerradas ---------------
    requisitos = {
        "V-01": "ningun contexto debe importar el adaptador HTTP de Usuario",
        "V-02": "AI ni Reminders deben alcanzar el proveedor de repositorios de Academic",
        "V-03": "AI no debe importar la entidad de dominio Task de Academic",
    }
    patrones = {
        "V-01": "usuario.adapters.inbound",
        "V-02": "academic.adapters.outbound.repository_provider",
        "V-03": "academic.domain.entities",
    }
    cerradas: dict[str, list[str]] = {}
    for clave, patron in patrones.items():
        infracciones: list[str] = []
        # Se recorre solo MODULES: `backend/app/main.py` es el composition root
        # y por definicion puede componer las implementaciones concretas.
        for archivo in MODULES.rglob("*.py"):
            texto = archivo.read_text(encoding="utf-8", errors="ignore")
            if patron not in texto:
                continue
            contexto = archivo.relative_to(MODULES).parts[0]
            if clave == "V-01" and contexto == "usuario":
                continue
            if clave == "V-02" and contexto == "academic":
                continue
            if clave == "V-03" and contexto == "academic":
                continue
            infracciones.append(str(archivo.relative_to(ROOT)).replace("\\", "/"))
        cerradas[clave] = infracciones
        if infracciones:
            anotar(
                clave,
                ROOT / infracciones[0],
                0,
                "{} ({} apariciones)".format(requisitos[clave], len(infracciones)),
            )

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
    ruta_base = Path(args.baseline)

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
        Path(args.json).write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("escrito: {}".format(args.json))

    return 0 if not regresiones else 1


if __name__ == "__main__":
    raise SystemExit(main())