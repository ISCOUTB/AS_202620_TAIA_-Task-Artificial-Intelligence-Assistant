# Verificación de dependencias y credenciales — S8

Esta nota responde al bloque de verificación de la entrega: que cada dependencia
declarada exista y sea la legítima, y que ninguna credencial real se haya
versionado. Todo lo afirmado aquí es reproducible con un comando, sin red.

```bash
python tools/verificar_dependencias.py
```

La salida completa queda en [`verificacion_dependencias.json`](verificacion_dependencias.json).

## Resultado actual

| Lock | Paquetes | Sin versión fijada | Sin hash |
| --- | --- | --- | --- |
| `backend/requirements.lock.txt` (producción) | 24 | 0 | 0 |
| `backend/requirements-dev.lock.txt` (desarrollo) | 31 | 0 | 0 |

Credenciales de producción en el árbol versionado: **0**.
Veredicto de la herramienta: **ok**.

## Defectos encontrados y corregidos

### D-DEP-01 — `python-dotenv` estaba afectado por una CVE

`backend/requirements.txt` fijaba `python-dotenv==1.1.1`. Esa versión tiene la
**CVE-2026-28684** (alias **PYSEC-2026-2270**, **GHSA-mf9w-mj56-hr94**):

> `set_key()` y `unset_key()` siguen enlaces simbólicos al reescribir un archivo
> `.env`. Si la ruta es un symlink y el directorio temporal está en otro sistema
> de archivos, `shutil.move()` degrada a `shutil.copy2()`, que escribe sobre el
> *destino del enlace* en lugar de reemplazarlo. Un atacante con permiso de
> escritura en el directorio puede provocar que un proceso con más privilegios
> sobrescriba cualquier archivo que ese proceso pueda escribir.

- Fecha del aviso: 2026-04-20. Corregida en **1.2.2**.
- Publicador legítimo: Saurabh Kumar (`theskumar`) y Bertrand Bonnefoy-Claudet (`bbc2`), repositorio `theskumar/python-dotenv`, licencia BSD-3-Clause.
- **Exposición real de TAIA: baja.** El único uso del proyecto es `load_dotenv()` en `backend/app/shared/adapters/outbound/database.py:10`; ni `set_key()` ni `unset_key()` se invocan en ningún parte del repositorio.
- **Decisión:** subir a **1.2.4** (la última publicada) en vez de solo documentar el riesgo. Es una actualización de parche dentro de la misma versión mayor y menor, y `load_dotenv()` se verificó con el mismo comportamiento antes y después.

Hashes verificados descargando la distribución y calculando SHA-256, y
contrastados con la API de PyPI:

| Distribución | SHA-256 |
| --- | --- |
| `python_dotenv-1.2.4-py3-none-any.whl` | `42269a8a5b3fd54ffa6f3d84b18abed50064717576b4ecf03dc4a55d8aa04fdc` |
| `python_dotenv-1.2.2-py3-none-any.whl` | `1d8214789a24de455a8b8bd8ae6fe3c6b69a5e3d64aa8a8e5d68e694bbcb285a` |

### D-DEP-02 — El lock de producción no tenía versión ni hash

`backend/requirements.lock.txt` terminaba en la línea

```
python-dotenv
```

sin `==` y sin `--hash`. Con `pip install --require-hashes` eso es un error
obligatorio, no una advertencia: la instalación de producción **no podía
funcionar** con verificación de hashes. El Dockerfile de la época tampoco pedía
`--require-hashes`, así que el defecto pasaba inadvertido: sin hashes, cualquier
versión de `python-dotenv` se instalaba, la vulnerable incluida.

### D-DEP-03 — Los lock files eran incompletos fuera de Linux

Ambos locks se generaron en Linux y omitían las dependencias que solo se
instalan en Windows. `psycopg[binary]` declara `tzdata` bajo
`sys_platform == "win32"`, y `pytest` declara `colorama` con el mismo marcador.
Al faltar en el lock, `pip install --require-hashes` aborta en Windows con:

```
ERROR: In --require-hashes mode, all requirements must have their versions
pinned with ==. These do not: tzdata from ... (from psycopg==3.3.6)
```

Esto explica por qué el CI en `ubuntu-latest` estaba verde mientras la
instalación local en Windows era imposible. Se añadieron con marcador y hash:

| Paquete | Versión | Marcador | SHA-256 del wheel |
| --- | --- | --- | --- |
| `tzdata` | 2026.5 | `sys_platform == "win32"` | `b683bd1b6659ddcd810ff02ad09ba821d4bf1065072805063eb35c49617905ac` |
| `colorama` | 0.4.6 | `sys_platform == "win32"` | `4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6` |

`tzdata` es un paquete de la **Python Software Foundation**
(`datetime-sig@python.org`), no está marcado como *yanked* y la API de PyPI no
reporta vulnerabilidades para 2026.5 ni para `colorama` 0.4.6.

### D-DEP-04 — Imagen de `uv` sin fijar en el Dockerfile

`backend/Dockerfile` copiaba el instalador desde
`ghcr.io/astral-sh/uv:latest`. La etiqueta `latest` es mutable: dos builds del
mismo `Dockerfile` en fechas distintas instalan binarios distintos, y eso rompe
la reproducibilidad que exige RNF-08 y la estrategia de calidad descrita en
[arc42 §4](arc42/04-estrategia-de-solucion.md).

Ahora queda fijada por etiqueta **y** por digest:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 /uv /uvx /bin/
RUN uv pip install --system --no-cache --require-hashes --only-binary :all: -r requirements.lock.txt
```

El digest se obtuvo del manifiesto OCI del registro. `--only-binary :all:`
impide además que se construya un paquete desde su código fuente en producción,
que es donde un lock con hashes ofrece menos garantía.

## Credenciales

La herramienta escanea los archivos versionados (`git ls-files`) buscando cinco
patrones de producción: clave de API de Gemini, URL de *pooler* de Supabase,
clave privada PEM, token de GitHub y JWT. Resultado: **0 hallazgos**.

Dos precisiones sobre el alcance de esa afirmación:

- **El escaneo cubre el árbol versionado**, no el historial completo. Para el historial se ejecutó `git log --all -S` sobre el patrón del *pooler* de Supabase y sobre el prefijo de la clave de Gemini: sin coincidencias. Ninguna credencial de producción entró en un commit.
- **Una credencial de producción sí fue compartida durante esta sesión por el estudiante**, en el canal de conversación, y llegó a escribirse en `backend/.env` antes de ser detectada y eliminada. Ese archivo está en `.gitignore:15`, nunca se versionó, y `git grep` confirma que no aparece en el índice. Aun así, la contraseña quedó expuesta fuera del repositorio y **debe rotarse**: rotar una contraseña filtrada fuera del control de versiones es responsabilidad de quien la expone, no del repositorio.

La lección de diseño que sí queda incorporada al código: `backend/app/shared/adapters/outbound/database.py:17` llama a `load_dotenv()` **en el momento de importar el módulo**. Cualquier comando del proyecto —`pytest`, `alembic upgrade head`, `run.bat`— abre automáticamente la base que esté en ese archivo. Por eso un `.env` mal escrito no es un error visible: es un `alembic upgrade head` apuntando a donde no debía. Las pruebas lo agravan, porque `backend/tests/conftest.py` ejecuta `command.downgrade(config, "base")` al iniciar la sesión.

## Cómo reproducir

```bash
python -m pip install --require-hashes --only-binary :all: -r backend/requirements-dev.lock.txt
python tools/verificar_dependencias.py
```

La primera orden es la que fallaba en Windows antes de D-DEP-03.