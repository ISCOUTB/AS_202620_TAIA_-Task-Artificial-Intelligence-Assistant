# Semana 7 — Evidencia condensada (contrato de API y pruebas)

> Este documento reúne, en un solo lugar, el contenido literal de los archivos que sustentan
> los criterios de la ficha S7, para que la evaluación no dependa de recorrer el árbol completo
> del repositorio. Todo lo citado aquí corresponde al commit `3c2ae726cec42371a88dbf28ff9a2f7bade43b46`
> (`origin/main`, 2026-09-16T21:40:14-05:00).

## 1. Contrato ejecutable versionado

`docs/api/openapi.json` — OpenAPI 3.1.0, versión `1.0.0`, 14 rutas:

```
/academic/tasks              [GET, POST]
/academic/tasks/{task_id}    [PATCH]
/academic/tasks/{task_id}/complete [PATCH]
/users                       [POST]
/users/login                 [POST]
/users/me                    [GET]
/users/me/telegram/link      [POST]
/users/telegram/link/confirm [POST]
/ai/message                  [POST]
/reminders                   [GET, POST]
/reminders/{reminder_id}     [GET, PATCH, DELETE]
/reminders/{reminder_id}/complete [POST]
/reminders/{reminder_id}/notify   [POST]
/health                      [GET]
```

Esquemas referenciados en `components/schemas`: `TaskCreateRequest`, `TaskResponse`,
`AIMessageRequest`, `AIMessageResponse`, `ErrorResponse`, `UserResponse`, `LoginResponse`,
entre otros — es decir, hay tipos de datos, no solo una lista de endpoints.

**Historial git del contrato:**
```
$ git log --format='%h %cI %s' -- docs/api/openapi.json
2837b47 2026-09-15T20:43:43-05:00 feat(api): add OpenAPI contract and contract tests
```
Incorporado a `main` mediante el merge `3c2ae72` (PR #15).

## 2. Correspondencia entre el contrato y la API implementada

`backend/tests/test_api_contract.py` contiene una prueba automatizada que compara el contrato
contra el esquema generado en vivo por la aplicación FastAPI (`app.openapi()`), no solo una
verificación manual de rutas:

```python
def _assert_contract_matches(contract: dict, implementation: dict) -> None:
    assert contract["openapi"].startswith("3.1.")
    assert contract["info"]["version"] == "1.0.0"
    assert contract["paths"] == implementation["paths"]
    assert contract["components"] == implementation["components"]
    assert contract["info"] == implementation["info"]

def test_openapi_contract_matches_implemented_api() -> None:
    contract = _load_contract()
    implementation = app.openapi()
    _assert_contract_matches(contract, implementation)
```

Resultado al ejecutarla localmente sobre este commit:

```
$ python -m pytest backend/tests/test_api_contract.py -v
test_openapi_contract_matches_implemented_api PASSED
test_contract_declares_paths_and_data_schemas PASSED
test_incompatible_change_is_detected PASSED
test_generated_client_contains_all_contract_operations PASSED
4 passed in 0.42s
```

Correspondencia verificada además a mano, ruta por ruta, contra el código:

| Ruta en el contrato | Router en el código |
|---|---|
| `POST /academic/tasks`, `GET /academic/tasks` | `backend/app/modules/academic/adapters/inbound/api.py` — `router = APIRouter(prefix="/academic/tasks", ...)` |
| `POST /users`, `POST /users/login`, `GET /users/me` | `backend/app/modules/usuario/adapters/inbound/api.py` — `router = APIRouter(prefix="/users", ...)` |
| `GET /health` | `backend/app/main.py` — `@app.get("/health")` |

## 3. El pipeline ejecuta la prueba de contrato

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install pip==26.2.1
          pip install --require-hashes --only-binary :all: -r backend/requirements-dev.lock.txt
      - name: Run tests
        run: python -m pytest backend/tests
      - name: Run API contract test
        run: python -m pytest backend/tests/test_api_contract.py -q
      - name: Regenerate API client from OpenAPI contract
        run: python tools/generate_api_client.py
      - name: Verify generated client is synchronized
        run: git diff --exit-code -- backend/generated/taia_api_client.py
```

**Run en verde para este commit:**
`https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions/runs/35175295373/job/105055575880`

- Workflow: `CI` · Job: `test` · **Resultado: succeeded** (Sep 17, 2026, 15s)
- Asociado al commit "Merge pull request #15 from ISCOUTB/val" (mismo commit calificado, `3c2ae72`)

Reproducción local de la suite completa sobre este mismo commit:
```
$ python -m pytest backend/tests -q
78 passed in 4.11s
```

## 4. Evidencia de que la prueba falla ante un cambio incompatible

`backend/tests/test_api_contract.py::test_incompatible_change_is_detected`:

```python
def test_incompatible_change_is_detected() -> None:
    """Demuestra que un cambio incompatible en el proveedor rompe la prueba."""
    contract = _load_contract()
    incompatible_implementation = copy.deepcopy(app.openapi())
    del incompatible_implementation["paths"]["/health"]

    with pytest.raises(AssertionError):
        _assert_contract_matches(contract, incompatible_implementation)
```

Complementado por `docs/evidencia_s7_contract_failure.txt` y el script de demostración
`tools/demo_contract_break.py`.

## 5. C4 nivel 2 con protocolo y formato en cada flecha

`docs/c4/C4-C2.md` — cada relación del diagrama Mermaid C4 está etiquetada con protocolo y formato:

```
BiRel(estudiante, telegram, "Escribe y recibe avisos", "Telegram Bot API / JSON")
Rel(estudiante, appmovil, "Consulta tareas", "HTTPS / JSON")
BiRel(telegram, api, "Webhook y mensajes", "HTTPS / JSON")
BiRel(api, gemini, "Interpreta", "HTTPS / JSON")
Rel(appmovil, api, "Consulta y registra", "HTTPS / JSON")
Rel(api, db, "Lee y escribe", "SQL/TCP 5432")
```

## 6. Tabla de aspectos (8 columnas)

`docs/aspectos.md` incluye las 8 columnas exigidas por el contrato del curso:
`ID · Aspecto · Requisito · C4 · ADR · Código · Pruebas · Evidencia`, con las filas A-01 a A-07,
todas con enlaces navegables a archivos reales del repositorio. La fila específica de esta semana:

```
| A-07 | Contrato e integración de la API principal | S7 — contrato OpenAPI 3.1, cliente
generado y prueba de contrato | C4-C2 | ADR-0002 | docs/api/openapi.json,
backend/generated/taia_api_client.py, tools/generate_api_client.py | test_api_contract.py |
evidencia_s7_contract_failure.txt, CI |
```

## 7. ADR de la estrategia de integración

`docs/adr/0002-estrategia-integracion-api-sincrona.md` documenta: escenario de calidad
relacionado (S1, S3, S4), opciones evaluadas A/B/C, decisión (HTTP síncrono + JSON + OpenAPI 3.1),
consecuencias, y trazabilidad a contrato, prueba y CI. Incluye alternativas descartadas
(mensajería/eventos, HTTP sin contrato) y su efecto de acoplamiento.

## 8. Registro de uso de IA — rechazos con motivo

`docs/ia.md` tiene 8 secciones `### Rechazado o modificado` con ítems concretos y su razón,
por ejemplo (Entrada 001):

```
### Rechazado o modificado
* Se descartó construir una aplicación exclusivamente de finanzas.
* Se redujo el alcance del MVP para concentrarse primero en el registro de tareas.
```

---

*Documento generado para acompañar la entrega de la semana 7 y facilitar la re-evaluación
de los criterios marcados como "No verificado" en la pasada temprana del autocalificador.*
