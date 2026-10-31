"""Verificacion reproducible del modelo de amenazas (S13).

Uso:
    python tools/verificar_modelo_amenazas.py
    python tools/verificar_modelo_amenazas.py --json docs/verificacion_amenazas.json

Comprueba, sin red, que docs/modelo_amenazas.md siga siendo una tabla de
amenazas priorizada y con mitigacion asignada:

  * cada amenaza de la seccion 2 tiene exactamente una fila en la seccion 3;
  * P e I estan en el rango 1..3 y la prioridad es P x I;
  * la tabla esta ordenada de mayor a menor prioridad;
  * toda fila de mitigacion tiene mitigacion, dueno, estado y evidencia;
  * el estado empieza por uno de los valores acordados;
  * cada enlace de evidencia apunta a un archivo que existe en el repositorio.

No valida los hashes de commit: el checkout de CI es superficial y los commits
antiguos no estarian disponibles. Los hashes se revisan a mano con git show.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "modelo_amenazas.md"

SECCION_AMENAZAS = "2. amenazas priorizadas"
SECCION_MITIGACIONES = "3. plan de mitigacion"

# Un estado valido empieza por uno de estos valores. "Hecha y activa en
# produccion" cuenta como "Hecha"; el matiz queda en el texto de la celda.
ESTADOS = ("hecha", "pendiente", "aceptada", "en curso")

COLUMNAS_AMENAZAS = ("id", "elemento c4", "stride", "owasp", "amenaza", "p", "i", "prio")
COLUMNAS_MITIGACIONES = ("id", "mitigacion", "dueno", "estado", "evidencia")

PATRON_ID = re.compile(r"^T-\d{2}$")
PATRON_ENLACE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
PATRON_SHA = re.compile(r"`[0-9a-f]{7,40}`")
PATRON_SEPARADOR = re.compile(r"^\|[\s:\-|]+\|$")


def _normalizar(texto: str) -> str:
    """Quita acentos y mayusculas para comparar encabezados y titulos."""

    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_acentos.lower().strip()


def _seccion(lineas: list[str], titulo: str) -> list[str] | None:
    inicio = None
    for indice, linea in enumerate(lineas):
        if linea.startswith("## ") and _normalizar(linea[3:]) == titulo:
            inicio = indice + 1
            break
    if inicio is None:
        return None

    for fin in range(inicio, len(lineas)):
        if lineas[fin].startswith("## "):
            return lineas[inicio:fin]
    return lineas[inicio:]


def _tabla(seccion: list[str]) -> tuple[list[str], list[list[str]]] | None:
    """Devuelve el encabezado y el cuerpo de la primera tabla de la seccion."""

    filas: list[str] = []
    for linea in seccion:
        limpia = linea.strip()
        if limpia.startswith("|"):
            filas.append(limpia)
        elif filas:
            break
    if len(filas) < 2:
        return None

    def celdas(fila: str) -> list[str]:
        return [celda.strip() for celda in fila.strip("|").split("|")]

    encabezado = celdas(filas[0])
    cuerpo = [celdas(fila) for fila in filas[1:] if not PATRON_SEPARADOR.match(fila)]
    return encabezado, cuerpo


def _indices(encabezado: list[str], requeridas: tuple[str, ...]) -> tuple[dict[str, int], list[str]]:
    # "Prio." y "Prio" son la misma columna: el punto final no cuenta.
    normalizado = [_normalizar(celda).rstrip(".").strip() for celda in encabezado]
    indices: dict[str, int] = {}
    faltantes: list[str] = []
    for columna in requeridas:
        if columna in normalizado:
            indices[columna] = normalizado.index(columna)
        else:
            faltantes.append(columna)
    return indices, faltantes


def _entero(valor: str) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def analizar(texto: str, raiz: Path, documento: str = "docs/modelo_amenazas.md") -> dict:
    """Analiza el documento y devuelve el resultado y la lista de problemas.

    `raiz` es el directorio del documento: los enlaces de evidencia se resuelven
    contra el, porque el modelo usa rutas relativas a docs/.
    """

    problemas: list[str] = []
    lineas = texto.splitlines()

    seccion_amenazas = _seccion(lineas, SECCION_AMENAZAS)
    seccion_mitigaciones = _seccion(lineas, SECCION_MITIGACIONES)
    if seccion_amenazas is None:
        problemas.append("no se encontro la seccion '## 2. Amenazas priorizadas'")
    if seccion_mitigaciones is None:
        problemas.append("no se encontro la seccion '## 3. Plan de mitigacion'")
    if problemas:
        return _resultado(documento, [], [], {}, {}, [], problemas)

    tabla_amenazas = _tabla(seccion_amenazas)
    tabla_mitigaciones = _tabla(seccion_mitigaciones)
    if tabla_amenazas is None:
        problemas.append("la seccion 2 no tiene una tabla markdown")
    if tabla_mitigaciones is None:
        problemas.append("la seccion 3 no tiene una tabla markdown")
    if problemas:
        return _resultado(documento, [], [], {}, {}, [], problemas)

    amenazas = _leer_amenazas(*tabla_amenazas, problemas)
    mitigaciones = _leer_mitigaciones(*tabla_mitigaciones, raiz, problemas)

    ids_amenazas = [fila["id"] for fila in amenazas]
    ids_mitigaciones = [fila["id"] for fila in mitigaciones]

    for identificador in sorted(set(ids_amenazas)):
        if ids_amenazas.count(identificador) > 1:
            problemas.append("la amenaza {} aparece mas de una vez en la seccion 2".format(identificador))
    for identificador in sorted(set(ids_mitigaciones)):
        if ids_mitigaciones.count(identificador) > 1:
            problemas.append("la mitigacion {} aparece mas de una vez en la seccion 3".format(identificador))

    sin_mitigacion = [i for i in ids_amenazas if i not in ids_mitigaciones]
    sin_amenaza = [i for i in ids_mitigaciones if i not in ids_amenazas]
    for identificador in sin_mitigacion:
        problemas.append("la amenaza {} no tiene fila de mitigacion".format(identificador))
    for identificador in sin_amenaza:
        problemas.append("la mitigacion {} no corresponde a ninguna amenaza".format(identificador))

    prioridades = [fila["prioridad"] for fila in amenazas if fila["prioridad"] is not None]
    fuera_de_orden = [
        amenazas[indice]["id"]
        for indice in range(1, len(prioridades))
        if prioridades[indice] > prioridades[indice - 1]
    ]
    for identificador in fuera_de_orden:
        problemas.append(
            "la amenaza {} rompe el orden: la tabla debe ir de mayor a menor prioridad".format(identificador)
        )

    por_prioridad: dict[str, int] = {}
    for fila in amenazas:
        clave = str(fila["prioridad"]) if fila["prioridad"] is not None else "desconocida"
        por_prioridad[clave] = por_prioridad.get(clave, 0) + 1

    por_estado: dict[str, int] = {}
    for fila in mitigaciones:
        clave = fila["estado"].split()[0] if fila["estado"] else "desconocido"
        por_estado[clave] = por_estado.get(clave, 0) + 1

    evidencias_inexistentes = [
        {"id": fila["id"], "enlace": enlace}
        for fila in mitigaciones
        for enlace in fila["evidencias_inexistentes"]
    ]

    return _resultado(
        documento, amenazas, mitigaciones, por_prioridad, por_estado, evidencias_inexistentes, problemas
    )


def _leer_amenazas(
    encabezado: list[str], filas: list[list[str]], problemas: list[str]
) -> list[dict]:
    indices, faltantes = _indices(encabezado, COLUMNAS_AMENAZAS)
    if faltantes:
        problemas.append("a la tabla de amenazas le faltan columnas: {}".format(", ".join(faltantes)))
        return []

    amenazas: list[dict] = []
    for numero, fila in enumerate(filas, start=1):
        valor = lambda columna: fila[indices[columna]] if indices[columna] < len(fila) else ""
        identificador = valor("id")
        if not PATRON_ID.match(identificador):
            problemas.append("fila {} de la seccion 2: id invalido '{}'".format(numero, identificador))
        for columna in ("elemento c4", "stride", "owasp", "amenaza"):
            if not valor(columna):
                problemas.append("{}: la columna '{}' esta vacia".format(identificador, columna))

        probabilidad = _entero(valor("p"))
        impacto = _entero(valor("i"))
        prioridad = _entero(valor("prio"))
        if probabilidad not in (1, 2, 3):
            problemas.append("{}: P debe ser 1, 2 o 3 (es '{}')".format(identificador, valor("p")))
        if impacto not in (1, 2, 3):
            problemas.append("{}: I debe ser 1, 2 o 3 (es '{}')".format(identificador, valor("i")))
        if probabilidad in (1, 2, 3) and impacto in (1, 2, 3):
            if prioridad != probabilidad * impacto:
                problemas.append(
                    "{}: la prioridad '{}' no es P x I ({} x {} = {})".format(
                        identificador, valor("prio"), probabilidad, impacto, probabilidad * impacto
                    )
                )

        amenazas.append(
            {
                "id": identificador,
                "elemento": valor("elemento c4"),
                "stride": valor("stride"),
                "owasp": valor("owasp"),
                "amenaza": valor("amenaza"),
                "probabilidad": probabilidad,
                "impacto": impacto,
                "prioridad": prioridad,
            }
        )
    return amenazas


def _leer_mitigaciones(
    encabezado: list[str], filas: list[list[str]], raiz: Path, problemas: list[str]
) -> list[dict]:
    indices, faltantes = _indices(encabezado, COLUMNAS_MITIGACIONES)
    if faltantes:
        problemas.append("a la tabla de mitigaciones le faltan columnas: {}".format(", ".join(faltantes)))
        return []

    mitigaciones: list[dict] = []
    for numero, fila in enumerate(filas, start=1):
        valor = lambda columna: fila[indices[columna]] if indices[columna] < len(fila) else ""
        identificador = valor("id")
        if not PATRON_ID.match(identificador):
            problemas.append("fila {} de la seccion 3: id invalido '{}'".format(numero, identificador))
        for columna in ("mitigacion", "dueno"):
            if not valor(columna):
                problemas.append("{}: la columna '{}' esta vacia".format(identificador, columna))

        estado = valor("estado")
        if not estado:
            problemas.append("{}: la columna 'estado' esta vacia".format(identificador))
        elif not _normalizar(estado).startswith(ESTADOS):
            problemas.append("{}: estado no reconocido '{}'".format(identificador, estado))

        evidencia = valor("evidencia")
        enlaces = PATRON_ENLACE.findall(evidencia)
        if not evidencia or (not enlaces and not PATRON_SHA.search(evidencia)):
            problemas.append("{}: la evidencia debe citar un archivo o un commit".format(identificador))

        inexistentes = [
            enlace
            for enlace in enlaces
            if not _enlace_existe(enlace, raiz)
        ]
        for enlace in inexistentes:
            problemas.append("{}: la evidencia '{}' no existe".format(identificador, enlace))

        mitigaciones.append(
            {
                "id": identificador,
                "mitigacion": valor("mitigacion"),
                "dueno": valor("dueno"),
                "estado": estado,
                "evidencia": evidencia,
                "evidencias_inexistentes": inexistentes,
            }
        )
    return mitigaciones


def _enlace_existe(enlace: str, raiz: Path) -> bool:
    objetivo = enlace.strip()
    if objetivo.startswith(("http://", "https://", "mailto:", "#")):
        return True
    ruta = objetivo.split("#", 1)[0]
    if not ruta:
        return True
    return (raiz / ruta).exists()


def _resultado(
    documento: str,
    amenazas: list[dict],
    mitigaciones: list[dict],
    por_prioridad: dict[str, int],
    por_estado: dict[str, int],
    evidencias_inexistentes: list[dict],
    problemas: list[str],
) -> dict:
    return {
        "documento": documento,
        "amenazas": len(amenazas),
        "mitigaciones": len(mitigaciones),
        "por_prioridad": dict(sorted(por_prioridad.items(), key=lambda par: par[0])),
        "por_estado": dict(sorted(por_estado.items())),
        "evidencias_inexistentes": evidencias_inexistentes,
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
    parser.add_argument("--doc", default=str(DOC), help="Documento a verificar (por defecto docs/modelo_amenazas.md).")
    parser.add_argument("--json", help="Ruta opcional para volcar el resultado.")
    args = parser.parse_args()

    documento = _ruta_en_repositorio(parser, args.doc)
    if not documento.is_file():
        parser.error("No existe el documento: {}".format(args.doc))

    resultado = analizar(
        documento.read_text(encoding="utf-8"),
        documento.parent,
        str(documento.relative_to(ROOT)).replace("\\", "/"),
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
