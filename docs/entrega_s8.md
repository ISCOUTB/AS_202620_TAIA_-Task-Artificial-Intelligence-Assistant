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
| Paquetes sin versión fijada ni hash | **0** de 55 | `python tools/verificar_dependencias.py` |
| Credenciales de producción versionadas | **0** | ídem |
| Infracciones de frontera nuevas | **0** | `python tools/audit_boundaries.py` |
| Suite completa al cierre | **202 pasan** | `pytest backend/tests` |

Las 364 variantes affirmativas combinan nueve palabras ("sí", "s", "dale",
"listo"…) con tres capitalizaciones y catorce envolturas ortográficas
(puntuación, espacios, comillas, rayas). Las 20 negativas incluyen casos que
se parecen a una confirmación: "sii", "no sé", "sí no", "listo no".

## Qué no se midió, y por qué

No hay `GEMINI_API_KEY` en este entorno. Se construyó el arnés y se dejó explícito
qué falta:

| Escenario | Estado | Qué haría falta |
| --- | --- | --- |
| **S1** exactitud de interpretación de intención | **Pendiente** | `GEMINI_API_KEY` y `python tools/eval_llm.py` |
| **S2** Confirmación de escrituras | **Medido** | nada; [`tools/eval_confirmacion.py`](../tools/eval_confirmacion.py) |
| **S3** Latencia p95 | **Parcial** | La confirmación sin red está medida (0,034 ms). La de extremo a extremo con Gemini, pendiente |
| **S4** Disponibilidad del asistente | **Pendiente** | despliegue y observación en el tiempo |
| **S5** Costo por intercambio | **Preparado** | `usageMetadata` registrado y arnés listo; falta la clave y el precio |

`tools/eval_llm.py` sin clave imprime que la medición está pendiente y sale con
código **2**, distinto del **1** de una corrida fallida. No se inventa ninguna
cifra. Los precios de token no están en el código: se pasan por parámetro,
porque cambian con frecuencia y una tabla desactualizada daría un costo
falsamente preciso.

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
| [ia.md](ia.md) | Entradas 011, 012 y 013: qué se pidió, qué se aceptó y qué se rechazó |
| [extracto_ia_s8.md](extracto_ia_s8.md) | Resumen ejecutivo de la trazabilidad de IA |
| [evaluacion_confirmacion.json](evaluacion_confirmacion.json) | Salida de la evaluación offline |
| [evaluacion_ia/dataset.jsonl](evaluacion_ia/dataset.jsonl) | 39 casos etiquetados para S1 y S3 |

## Cómo reproducir toda la entrega

```bash
python tools/verificar_dependencias.py    # dependencias y credenciales
python tools/audit_boundaries.py          # fronteras y composicion
python tools/eval_confirmacion.py         # S2 y latencia sin red
python tools/eval_llm.py --dry-run         # integridad del dataset, sin clave
pytest backend/tests                      # 202 pruebas
```

Todos salen con código cero en el estado actual, salvo `eval_llm.py` sin
`GEMINI_API_KEY`, que sale con código 2 a propósito.

## Lo que queda para cerrar la semana

1. Definir `GEMINI_API_KEY` y ejecutar `tools/eval_llm.py` para S1, S3 y S5.
2. Rotar la contraseña de producción de Supabase, expuesta fuera del repositorio.
3. Cerrar E-02, moviendo la composición de Reminders y de `structure_api` al
   composition root.
4. Cerrar E-05 haciendo que el puerto de Academic exponga la traducción del
   texto libre al estado canónico.
5. Dar profundidad a `/health` (E-06) para que la comprobación de CD detecte una
   base de datos inaccesible.