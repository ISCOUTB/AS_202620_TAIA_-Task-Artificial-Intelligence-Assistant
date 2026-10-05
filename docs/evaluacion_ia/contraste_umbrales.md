# Contraste de las mediciones con los umbrales de S1 y S3

Este documento contrasta, en un solo lugar, lo que se midió para la porción construida con apoyo de IA con el umbral de cada escenario asociado, y declara qué parte de cada escenario queda sin medir.

## Porción y escenarios asociados

**Porción:** confirmación de escrituras en lenguaje natural, defecto D-S8-01 ([ADR-0005](../adr/0005-normalizacion-confirmacion-espanol.md), `_normalizar_respuesta` en `backend/app/modules/ai/application/use_cases/handle_message.py`).

**Escenarios asociados**, según ADR-0005 y [escenarios_calidad.md](../calidad/escenarios_calidad.md):

- **S1 — Registro correcto de información académica.** Al menos el 90 % de los campos esperados deben identificarse y registrarse correctamente en una muestra de 100 mensajes académicos representativos.
- **S3 — Respuesta del asistente ante un mensaje.** El 95 % de las solicitudes debe recibir respuesta en ≤ 7 s, desde la recepción en el backend hasta el envío al canal del estudiante.

**Artefactos usados:**

| Artefacto | Qué contiene | Generado |
| --- | --- | --- |
| [`resultado_s1_100.json`](resultado_s1_100.json) | Interpretación con el modelo real: 99 mensajes y 110 campos etiquetados | `tools/eval_llm.py` con `gemini-3.5-flash-lite`, 2026-10-05 04:17 UTC, sobre `4bfbadb` con el conjunto ampliado (la `procedencia` del JSON registra los hashes del conjunto y del arnés). El hash del conjunto corresponde a la versión anterior a la revisión: la revisión no cambió ninguna etiqueta, solo el campo `revision`, que el arnés ignora. |
| [`evaluacion_confirmacion.json`](../evaluacion_confirmacion.json) | Etapa de confirmación, sin red ni modelo: 384 respuestas | `tools/eval_confirmacion.py`, commit `70ee6e3` |
| [`resultado_s1_s3.json`](resultado_s1_s3.json) | Histórico: 39 mensajes, solo intención | `tools/eval_llm.py`, 2026-10-04 ([ia.md, entrada 014](../ia.md)). Se conserva como referencia. |

## Contraste

| Escenario | Umbral | Qué se midió | Resultado | Contraste |
| --- | --- | --- | --- | --- |
| **S1**, extracción de campos | ≥ 90 % de campos en 100 mensajes | Campos extraídos por el modelo: 110 campos en 99 mensajes | **91,8 %** (101 de 110) | **Supera el umbral** por 1,8 puntos en la extracción. Las etiquetas fueron revisadas por el equipo el 2026-10-05, sin cambios. |
| **S1**, registro en PostgreSQL | Mismo umbral, sobre lo **registrado** | No medido | — | **No verificado.** El arnés no confirma ni persiste. **S1 completo no queda demostrado.** |
| **S1**, etapa de confirmación (la porción) | La confirmación no debe hacer perder registros correctos ni crear incorrectos | 364 confirmaciones afirmativas y 20 negativas | **364 de 364** aceptadas; **0 de 20** escrituras indebidas | La etapa no resta exactitud a S1. Antes de D-S8-01 perdía las 7 variantes con tilde de cada 16 casos de prueba. |
| **S3**, extremo a extremo | p95 ≤ 7 000 ms, del backend al canal | No medido | — | **No verificado.** `GET /metrics` del despliegue no registraba ninguna petición a `POST /ai/message` al consultarlo el 2026-10-04. |
| **S3**, tramo del modelo | Mismo presupuesto | Llamada a Gemini, 99 intentos desde el equipo del estudiante, incluido el fallido | p50 1 742,6 ms · **p95 2 191,0 ms** · máx. 20 209,5 ms | **Dentro del umbral** en p95: consume el 31,3 % del presupuesto. El máximo supera los 7 s (ver la lectura de S3). |
| **S3**, etapa de confirmación (la porción) | Mismo presupuesto | 384 muestras, en proceso | **p95 0,0338 ms** | Despreciable. La confirmación no llama al modelo. |

**Otras cifras de la misma corrida:**

- Intención correcta en el 88,89 % de los mensajes (88 de 99).
- 1 error de llamada (`c008`).
- Costo de 0,03378 USD en 99 intentos, unos 0,000341 USD por operación, con 0,30 USD y 2,50 USD por millón de tokens de entrada y de salida. La cobertura de tokens es incompleta porque el intento fallido no devolvió consumo.

## Lectura de los resultados

### S1: dónde falla la extracción

| Campo | Correctos | Lectura |
| --- | --- | --- |
| Título | 37 de 38 | El único fallo, `c006`, es probablemente una **etiqueta errónea del conjunto original**: el texto dice «deElles» y la etiqueta espera «de ellas». |
| Fecha (`due_at`) | 37 de 37 | Incluidos los dos `null` deliberados: el modelo no inventó ni fecha ni título. |
| Materia | 14 de 14 | — |
| Referencia de tarea | 12 de 15 | Dos fallos vienen de errores de intención (`u002`, `u008`). En `u010` el modelo devolvió «el proyecto integrador»: Academic busca con `icontains`, así que **esa tarea no se encontraría**. |
| Estado | **1 de 6** | **El punto débil.** En `q008` el modelo devolvió «completadas» en lugar de `completed`. Academic solo traduce `done`, `completed`, `pending` y `overdue`, así que **el filtro se descarta y el estudiante ve todas sus tareas**. En los otros cuatro fallos el modelo no extrajo el estado o lo confundió. El prompt de `gemini_llm.py` no indica qué vocabulario de estado usar. |

Sin los estados, la exactitud es del 96,2 % (100 de 104). Por origen de las etiquetas: 10 de 14 en los campos del conjunto original y 91 de 96 en los añadidos.

### S1: intención y la porción

De los 11 fallos de intención, 5 son mensajes que el modelo leyó como `create_task` sin que lo pidieran (`c007`, `s004`, `s005`, `s008`) o cuando pedían modificar (`u008`). Es justamente el caso que contiene la porción: una interpretación errónea de alta, como mucho, genera una **propuesta** que exige un «sí» explícito, no un registro. La confirmación no corrige al modelo, pero impide que esos errores lleguen a PostgreSQL sin que el estudiante los vea.

### S3

El p95 del tramo del modelo queda dentro del presupuesto, pero **un intento de 99 (`c008`) agotó el timeout de 20 s** del adaptador y terminó en `LLMError`. Es la evidencia empírica de la consecuencia negativa registrada en [ADR-0007](../adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md): un proveedor colgado deja al estudiante esperando hasta 20 s, por encima de los 7 s del escenario. Con una de cada cien peticiones no se rompe el p95, pero con dos o más sí.

## Lo que falta para cerrar cada escenario

| Escenario | Falta | Requiere |
| --- | --- | --- |
| S1 | Decidir si la etiqueta de `c006`, del conjunto original, es errónea y, si se corrige, volver a ejecutar el arnés. | Unos 10 minutos de ejecución, con un costo de unos 0,03 USD. |
| S1 | Comprobar los campos **persistidos**, no solo los extraídos. | Recorrido confirmado contra una base PostgreSQL de pruebas. |
| S1 | Fijar el vocabulario de estado en el prompt, o traducir los sinónimos en español en Academic (defecto observado en `q008`). | Decisión del equipo y su prueba roja y verde. |
| S3 | Muestras reales de `POST /ai/message` en el despliegue, leídas en `GET /metrics`. | Desplegar la corrección del NULL en conversaciones ([diagnóstico](diagnostico_conversations_null.md)) y la clave del proveedor en el entorno de Dokploy. |
| S3 | Revisar el timeout de 20 s frente al umbral de 7 s. | Revisión de ADR-0007. |

## Convención de etiquetado del conjunto

El arnés compara cada campo de forma estricta: título y materia como texto, sin distinguir mayúsculas pero sí tildes; las fechas, como instante exacto. Por eso solo se etiqueta lo que tiene una única respuesta correcta.

- **Referencia temporal:** jueves 2026-09-10 12:00 −05:00 (`AHORA` en `tools/eval_llm.py`).
- **Día sin hora:** se espera las 23:59 de ese día (regla 3 del prompt de `gemini_llm.py`).
- **No se etiquetan las fechas ambiguas:** «el jueves» (¿hoy o el siguiente?), «esta semana», «para mañana» en una consulta, porque los límites del rango no son únicos.
- **Materia:** solo cuando el mensaje la separa de forma explícita («materia», «asignatura», «clase de»). Si no, forma parte del título.
- **Título:** el nombre de la tarea sin el verbo, la fecha ni la materia explícita.
- **`null` deliberado:** `c036` (sin fecha) y `c037` (sin título) miden si el modelo inventa datos que el mensaje no trae.
- **Estado:** el vocabulario que acepta Academic (`pending`, `completed`, `overdue`).
- **Procedencia:** los casos `c009`–`c038`, `q010`–`q019`, `u006`–`u015`, `h005`–`h007`, `x009`–`x012` y `s006`–`s009` se redactaron con apoyo de IA y el equipo los revisó el 2026-10-05; llevan `"revision": "revisado"`. El arnés ignora ese campo.

## Reproducción

```bash
python tools/eval_confirmacion.py --json docs/evaluacion_confirmacion.json
python tools/eval_llm.py --dry-run
python tools/eval_llm.py --json docs/evaluacion_ia/resultado_s1_100.json --precio-input 0.30 --precio-output 2.50
```

El segundo comando no llama al modelo. El tercero exige `GEMINI_API_KEY`; sin ella termina con código 2 y no escribe cifras. Termina con código 1 si alguna llamada falla: el fallo se contabiliza en las métricas y no invalida la corrida.
