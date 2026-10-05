# Entrega S8 — Confirmación de escrituras, verificación y auditoría

Este documento es el índice y el cierre de la entrega de la Semana 8. Todo lo que
afirma aquí es reproducible con un comando; donde no se pudo medir, se dice
explícitamente que no se midió.

Rama: `Mark`. `main` y `origin/main` siguen en `4b07242` y no se tocaron.

## Qué se entregó

Una porción real del producto corregida con un ciclo rojo-verde comprobable: la
**confirmación de escrituras por lenguaje natural**. Un estudiante escribía
"Sí", con tilde o sin ella, y la tarea nunca se creaba.

El defecto era de una línea y estaba en dos sitios relacionados:

```python
_YES = {"si", "s", "dale", "ok", "confirmo", "yes", "listo", "hazlo"}
# ...
return text.lower().strip(" .!?")
```

`.lower()` convierte "Sí" en "sí", que no coincide con el `"si"` sin tilde del
conjunto. `[AFLTA-1]` La comparación fallaba y `_resolve_pending` devolvía
"no confirmed", así que la tarea se perdía sin error ni aviso.

La corrección es una función auxiliar que normaliza con `unicodedata`,
`casefold()` y eliminación de signos en los extremos. Se documentó en
[ADR-0005](adr/0005-normalizacion-confirmacion-espanol.md).

## Resultados

| Medición | Resultado | Cómo reproducir |
| --- | --- | --- |
| Línea base antes del defecto | 171 pruebas | `docs/evidencia_s8_baseline.txt` |
| Con el defecto presente | 7 fallan, 9 pasan | `docs/evidencia_s8_pre-fix.txt` |
| Caso nuevo tras el arreglo | 16 pasan | `pytest backend/tests/test_ai_create_task_confirmation.py` |
| Suite completa tras el arreglo | 187 pasan | `docs/evidencia_s8_post-fix.txt` |
| Variantes afirmativas aceptadas | **364 de 364** (100 %) | `python tools/eval_confirmacion.py` |
| Respuestas negativas que crearon una tarea | **0 de 20** (0 %) | ídem |
| Latencia de la confirmación | p50 0,014 ms · p95 0,034 ms | ídem |
| **S1** exactitud de intención | **32 de 39** (82,05 %) | `docs/evaluacion_ia/resultado_s1_s3.json` |
| **S3** latencia de la llamada al modelo | p50 1 293,3 ms · p95 1 618,8 ms · máx 1 687,5 ms | ídem, 39 muestras |
| **S5** tokens y costo | 16 302 de entrada · 2 915 de salida | ídem |
| **S5** costo por operación | **0,000312 USD** (0,012178 USD las 39) | ídem |
| Paquetes sin versión fijada ni hash | **0** de 55 | `python tools/verificar_dependencias.py` |
| Credenciales de producción versionadas | **0** | ídem |
| Infracciones de frontera nuevas | **0** | `python tools/audit_boundaries.py` |
| Suite completa al cierre | **202 pasan** | `pytest backend/tests` |

Las 364 variantes affirmativas combinan nueve palabras ("sí", "s", "dale",
"listo"…) con tres capitalizaciones y catorce envolturas ortográficas
(puntuación, espacios, comillas, rayas). Las 20 negativas incluyen casos que
se parecen a una confirmación: "sii", "no sé", "sí no", "listo no".

## El componente generativo sí se midió

El sistema incorpora un componente generativo —el clasificador de intención y la
extracción de campos que produce `GeminiLLM`—, así que le corresponde un
conjunto de evaluación con resultados. Ese conjunto es
[`docs/evaluacion_ia/dataset.jsonl`](evaluacion_ia/dataset.jsonl): **39 casos
etiquetados** a mano, repartidos en cinco intenciones (6 `create_task`, 9
`query_tasks`, 5 `update_task`, 3 `system_help`, 16 `unknown`). El arnés es
[`tools/eval_llm.py`](../tools/eval_llm.py) y su salida es
[`resultado_s1_s3.json`](evaluacion_ia/resultado_s1_s3.json).

La corrida se hizo el **2026-10-04** contra **`gemini-3.5-flash-lite`**, con los
precios declarados de **0,30 USD** de entrada y **2,50 USD** de salida por millón
de tokens, tomados de la tabla de ese modelo en la documentación de Google el
mismo día. Treinta y nueve llamadas, **ningún error**.

| Métrica | Valor | Lectura |
| --- | --- | --- |
| **S1** exactitud de intención | **82,05 %** (32 de 39) | El conjunto de estilos domina: `create_task`, `query_tasks` y `system_help` al 100 % |
| **S3** latencia de la llamada | p50 **1 293,3 ms** · p95 **1 618,8 ms** · máx **1 687,5 ms** | 39 muestras, ninguna descartada |
| **S5** tokens | 16 302 de entrada · 2 915 de salida | 418 de entrada y 75 de salida por operación, de media |
| **S5** costo | **0,012178 USD** en total | **0,000312 USD por operación** |

### Qué falla, y por qué importa más que el promedio

Los siete fallos están concentrados y no se reparten al azar:

| Intención esperada | Casos | Aciertos | Exactitud |
| --- | --- | --- | --- |
| `create_task` | 6 | 6 | 100 % |
| `query_tasks` | 9 | 9 | 100 % |
| `system_help` | 3 | 3 | 100 % |
| `update_task` | 5 | 4 | 80 % |
| **`unknown`** | **16** | **10** | **62,5 %** |

Cinco de los siete fallos son `unknown` que el modelo contesta como
`create_task` (`c007`, `c008`, `s004`, `s005`) o como `system_help` (`h004`,
`x007`). El séptimo es `u002`, un `update_task` que vuelve como `unknown` y
pierde la referencia de la tarea.

Esto **no** es un defecto uniforme del modelo, y por eso el 82,05 % por sí solo no
alcanza para decidir. El comportamiento que queda en pie es
**sobreinterpretar**: ante un texto que no encaja en ninguna intención, elegir
crear una tarea. En el producto esa sobreinterpretación no es inocua, porque
`create_task` es la única intención cuya confirmación desemboca en una
escritura. Un `unknown` que se convierte en `create_task` pide al estudiante que
confirme una tarea que nunca pidió. El sistema no escribe nada sin confirmación,
así que el daño es una pregunta extra, no un dato perdido; pero es exactamente el
modo de fallo que la normalización de
[ADR-0005](adr/0005-normalizacion-confirmacion-espanol.md) elimina en la última
barriera.

### Tres límites de esta medición, declarados

1. **S1 no es comparable con el escenario tal como está escrito.** El escenario
   habla de extraer los campos correctos en 100 mensajes. Lo que se midió es la
   **intención** sobre 39 mensajes, y el único campo que se contrasta de forma
   individual es `task_hint` de `u002`. La extracción de título y fecha no tiene
   conjunto de evaluación propio.
2. **S3 no es de extremo a extremo.** Mide el tramo desde la máquina del
   estudiante hasta la respuesta del modelo, con la red de casa y el proceso de
   Python dentro del reloj. No incluye Telegram, ni el gateway académico, ni la
   base de datos. El p95 de 1,62 s es una cota optimista de lo que verá el
   estudiante.
3. **El denominador de S1 incluye un caso que el dataset declara inválido.**
   `dataset.jsonl:28` (`x002`) tiene el texto vacío y la nota «vacío, se rechaza
   antes del modelo», pero `tools/eval_llm.py` no implementa ese descarte: lo envía
   al modelo como cualquier otro. El modelo lo respondió `unknown`, así que
   cuenta como acierto y no bajó el promedio. Si se aplicara el filtro,
   S1 sería 32 de 38, un **84,2 %**. Se reporta 82,05 % porque es lo que el
   arnés midió, y la deuda técnica queda anotada en la
   [bitácora](bitacora_s8.md).

### Un límite sobre la trazabilidad del artefacto

`resultado_s1_s3.json` **no registra qué modelo lo produjo**, ni la fecha, ni el
commit: `eval_llm.py` solo escribe las métricas. El modelo, la fecha y los
precios están declarados en las líneas de arriba, que es la fuente que debe
usarse. Cerrar eso —que el JSON sea auto-descriptivo— es trabajo pendiente del
arnés, no de esta corrida: un artefacto de medición no se retoca a mano después
de haberlo producido.

## Qué no se midió, y por qué

| Escenario | Estado | Qué haría falta |
| --- | --- | --- |
| **S1** exactitud de interpretación de intención | **Medido** | 82,05 % (32 de 39), con los límites de la sección anterior |
| **S2** Confirmación de escrituras | **Medido** | nada; [`tools/eval_confirmacion.py`](../tools/eval_confirmacion.py) |
| **S3** Latencia p95 | **Medido** | El tramo del modelo, p95 1 618,8 ms. El de extremo a extremo, no |
| **S4** Disponibilidad del asistente | **Pendiente** | despliegue desde `main` y observación en el tiempo |
| **S5** Costo por intercambio | **Medido** | 0,000312 USD por operación, a los precios declarados |

Un escenario queda pendiente y no se disfraza de medido: **S4**, la
disponibilidad, requiere observación en el tiempo sobre un despliegue real.

`tools/eval_llm.py` **sigue** saliendo con código **2** cuando no hay
`GEMINI_API_KEY`, en lugar de inventar cifras: esa rama no se tocó. Los precios
de token **no** están en el código: se pasan por parámetro, porque cambian con
frecuencia y una tabla desactualizada daría un costo falsamente preciso.

## Defectos encontrados y cerrados

| ID | Defecto | Gravedad | Estado |
| --- | --- | --- | --- |
| **D-S8-01** | "Sí" con tilde nunca confirma; la tarea se pierde | Alta | Corregido, commit `9160c4b` |
| **D-DEP-01** | `python-dotenv==1.1.1` afectada por CVE-2026-28684 | Media | Corregido a 1.2.4 |
| **D-DEP-02** | `requirements.lock.txt` con `python-dotenv` sin versión ni hash | Alta | Corregido |
| **D-DEP-03** | Locks sin dependencias de Windows: instalación local imposible | Alta | Corregido |
| **D-DEP-04** | `uv:latest` en el Dockerfile, etiqueta mutable | Media | Corregido por digest |
| **E-01** | `httpx.Client` nuevo por petición y nunca cerrado | Alta | Corregido |
| **E-02** | Composición fuera del composition root | Media | Parcial; R1 en línea base |
| **E-03** | Colaboradores construidos al importar el módulo | Media | Corregido |
| **E-04** | Falta de clave → 503 por petición con `/health` en `ok` | Media | Corregido |
| **E-05** | V-03 de S6 no estaba del todo cerrada | Baja | **Abierta**, documentada |
| **E-06** | `/health` no comprueba base de datos ni adaptadores | Baja | Anotada, fuera de alcance |
| **CFG-01** | `run.bat` publicaba un secreto JWT por defecto | Alta | Corregido |
| **CFG-02** | `.gitignore` ignoraba la plantilla de configuración | Media | Corregido |

Los detalles completos están en
[`verificacion_dependencias_s8.md`](verificacion_dependencias_s8.md) y
[`auditoria_erosion.md`](auditoria_erosion.md).

## Sobre la auditoría de S6

La auditoría de S6 cerró V-01 a V-04 y su evidencia de cierre no es reproducible
sobre el código actual. Afirma que no hay imports de `AI` hacia
`academic.domain.entities.task`, y `ai/adapters/outbound/academic_gateway.py:19`
importa `TaskStatus`. Afirma que la composición está concentrada en `main.py`, y
Reminders y `structure_api` de Academic componen en su propio adaptador HTTP.

El hallazgo importante no es que las afirmaciones fueran falsas, sino que
**ninguna estaba respaldada por una comprobación automática**. Por eso
[`tools/audit_boundaries.py`](../tools/audit_boundaries.py) existe: ocho reglas
que se ejecutan sin red y sin base de datos, con una línea base para que el
comando distinga lo ya triado de una regresión.

## Una decisión que conviene conocer

La confirmación ya no depende del modelo de lenguaje. Es la última barrera antes
de escribir en la base de datos, y una barrera que depende de un componente no
determinista es una barrera que falla de forma intermitente e imposible de
reproducir. La normalización es pura, rápida y testeable.

El coste es que el asistente ya no "entiende" confirmaciones exóticas. Se
documenta en ADR-0005: un mensaje que no reduzca a un sí o un no conocido
devuelve "no confirmed" y **no** escribe nada. Ante la duda, no escribir.

## Trazabilidad

| Documento | Contenido |
| --- | --- |
| [bitacora_s8.md](bitacora_s8.md) | Recorrido paso a paso y dónde está cada evidencia, incluidas las corridas rojas |
| [ADR-0005](adr/0005-normalizacion-confirmacion-espanol.md) | Por qué normalizar en vez de enumerar o preguntar al modelo |
| [verificacion_dependencias_s8.md](verificacion_dependencias_s8.md) | Dependencias, CVE y credenciales |
| [auditoria_erosion.md](auditoria_erosion.md) | E-01 a E-06 y el auditor que los detecta |
| [ia.md](ia.md) | Entradas 011, 012, 013 y 014: qué se pidió, qué se aceptó y qué se rechazó |
| [extracto_ia_s8.md](extracto_ia_s8.md) | Resumen ejecutivo de la trazabilidad de IA |
| [evaluacion_confirmacion.json](evaluacion_confirmacion.json) | Salida de la evaluación offline |
| [evaluacion_ia/dataset.jsonl](evaluacion_ia/dataset.jsonl) | 39 casos etiquetados para S1 y S3 |
| [evaluacion_ia/resultado_s1_s3.json](evaluacion_ia/resultado_s1_s3.json) | Salida de la evaluación con Gemini: S1, S3 y S5 |

## Cómo reproducir toda la entrega

```bash
python tools/verificar_dependencias.py    # dependencias y credenciales
python tools/audit_boundaries.py          # fronteras y composicion
python tools/eval_confirmacion.py         # S2 y latencia sin red
python tools/eval_llm.py --dry-run         # integridad del dataset, sin clave
pytest backend/tests                      # 202 pruebas
```

Y, solo con `GEMINI_API_KEY` definida en `backend/.env`, la corrida que produjo
S1, S3 y S5:

```bash
python tools/eval_llm.py \
  --precio-input 0.30 --precio-output 2.50 \
  --json docs/evaluacion_ia/resultado_s1_s3.json
```

Tarda unos cuatro minutos: el arnés espera seis segundos entre llamadas para no
probar el límite por minuto del nivel gratuito. Los precios se pasan por
argumento a propósito, y hay que volver a consultarlos: los de arriba son los
declarados el 2026-10-04 y no son parte del código.

Todos los comandos sin red salen con código cero en el estado actual.
`eval_llm.py` **sin** `GEMINI_API_KEY` sale con código 2 a propósito, y es lo
único que devuelve un código distinto de cero.

## Lo que queda para cerrar la semana

1. **S4, disponibilidad del asistente.** Es lo único que falta por medir: exige
   desplegar desde `main` y observar en el tiempo. No se aproximó con una
   estimación.
2. **Manejar el 429 en el adaptador.** El nivel gratuito de Gemini limita las
   llamadas por minuto y una ráfaga produce `LLMError` sin explicar nada al
   estudiante. La evaluación sortea el problema con una pausa; el producto no lo
   sortea. Riesgo abierto en
   [`arc42/11`](arc42/11-riesgos-y-deudas-tecnicas.md).
3. **Cerrar E-02**, moviendo la composición de Reminders y de `structure_api` al
   composition root.
4. **Cerrar E-05** haciendo que el puerto de Academic exponga la traducción del
   texto libre al estado canónico.
5. **Dar profundidad a `/health`** (E-06) para que la comprobación de CD detecte
   una base de datos inaccesible.

Y dos cosas que ya no están en la lista porque se hicieron: `GEMINI_API_KEY`
está definida y `tools/eval_llm.py` corrió, y la contraseña de producción de
Supabase **ya fue rotada** por el estudiante, como se registra en
[`verificacion_dependencias_s8.md`](verificacion_dependencias_s8.md).
