# Mediciones de latencia

Este documento reúne las mediciones de latencia de TAIA, explica qué es el p95 y contrasta cada valor con su objetivo. No va en la presentación; es el respaldo de lo que se diga sobre rendimiento.

## Qué es el p95

El **p95 (percentil 95)** es el tiempo por debajo del cual queda el 95 % de las respuestas. Si se miden 100 respuestas y se ordenan de la más rápida a la más lenta, el p95 es la respuesta número 95: solo 5 de cada 100 tardan más que ese valor.

Ejemplo: si el p95 del asistente es 1 200 ms, 95 de cada 100 mensajes se responden en 1,2 s o menos.

**Por qué se usa en lugar del promedio:** el promedio esconde a los usuarios con peor suerte. Con 95 respuestas de 1 s y 5 de 20 s, el promedio da 1,95 s y parece aceptable, pero 1 de cada 20 estudiantes espera 20 s. El p95 sí refleja esa cola. Además, un solo valor extremo mueve mucho el promedio y casi nada el p95.

**El p50 (mediana)** es la respuesta del medio: la experiencia típica. El p95 es la experiencia "mala pero frecuente". El máximo es el peor caso observado.

**Cómo se calcula en TAIA:** por rango más próximo. Se ordenan las muestras y se toma la de la posición `ceil(0,95 × n)`. Lo usan tanto el arnés de evaluación (`tools/eval_llm.py`) como la métrica de la API (`backend/app/shared/adapters/inbound/observability.py`).

## Objetivos

| Qué se mide | Objetivo | Origen |
|---|---|---|
| Respuesta del asistente (`POST /ai/message`) | p95 ≤ 7 000 ms | Escenario S3 ([escenarios_calidad.md](escenarios_calidad.md)) |
| Operaciones CRUD (resto de rutas) | p95 < 500 ms | RNF-08 ([requerimientos.md](../requerimientos.md)) |

Nota: RNF-08 también dice "respuesta del agente con p95 < 8 s", mientras que S3 y el código (`AGENT_TARGET_MS = 7000`) usan 7 s. Se toma el valor más estricto (7 s); conviene alinear el texto de RNF-08.

## Mediciones del tramo del modelo (LLM)

Es el tiempo de la llamada al proveedor (Groq o Gemini) para interpretar un mensaje: el componente más lento del asistente. Se midió con `tools/eval_llm.py` desde el equipo del estudiante, sobre el conjunto de evaluación de S1, contando todos los intentos (también los fallidos).

| Fecha | Proveedor y modelo | Muestras | Errores | p50 | **p95** | Máximo | Fuente |
|---|---|---:|---:|---:|---:|---:|---|
| 2026-10-31 | Groq `openai/gpt-oss-120b` | 99 | 0 | 852,6 ms | **1 198,7 ms** | 1 489,0 ms | [resultado_groq_s1_100_con_dia.json](../evaluacion_ia/resultado_groq_s1_100_con_dia.json) |
| 2026-11-21 | Groq `openai/gpt-oss-120b` | 114 | 0 | 873,4 ms | **1 358,1 ms** | 1 884,7 ms | [resultado_groq_s16.json](../evaluacion_ia/resultado_groq_s16.json) |
| 2026-10-31 | Gemini `gemini-3.5-flash-lite` | 99 | 0 | 1 254,0 ms | **1 690,3 ms** | 3 425,1 ms | [resultado_gemini_s1_100_con_dia.json](../evaluacion_ia/resultado_gemini_s1_100_con_dia.json) |
| 2026-11-23 | Gemini `gemini-3.5-flash-lite` (conjunto con voz) | 116 | 4 | 1 672,5 ms | **3 572,1 ms** | 10 268,3 ms | [resultado_gemini_voz.json](../evaluacion_ia/resultado_gemini_voz.json) |
| 2026-10-05 | Gemini `gemini-3.5-flash-lite` | 99 | 1 | 1 742,6 ms | **2 191,0 ms** | 20 209,5 ms | [resultado_s1_100.json](../evaluacion_ia/resultado_s1_100.json) |

**Lectura:**

- Groq, el proveedor principal desde [ADR-0013](../adr/0013-usar-groq-como-proveedor-llm-principal.md), tiene el p95 más bajo: entre 1,2 s y 1,4 s, menos del 20 % del presupuesto de 7 s.
- Todos los p95 quedan dentro de los 7 s.
- Los máximos de Gemini muestran el riesgo de la cola: un intento agotó el timeout de 20 s (2026-10-05) y otro llegó a 10,3 s (2026-11-23). Con 1 caso de 100 no se rompe el p95; con 5 o más sí.

## Confirmación de una acción

Cuando el estudiante responde "sí" a una propuesta, TAIA no vuelve a llamar al LLM: compara la respuesta con una lista fija.

| Muestras | p50 | **p95** | Máximo | Fuente |
|---:|---:|---:|---:|---|
| 384 | 0,014 ms | **0,034 ms** | 0,169 ms | [bitacora_s8.md](../bitacora_s8.md), [evaluacion_confirmacion.json](../evaluacion_confirmacion.json) |

Es despreciable frente al presupuesto de S3.

## Evidencia en producción

- **2026-10-30, 22:47:** Gemini respondió `503` después de unos 8,6 s y Groq respondió en 0,7 s. `POST /ai/message` tardó 9 337 ms en total, por encima de los 7 s de S3, pero el mensaje se atendió. Riesgo aceptado en [arc42 §11.14](../arc42/11-riesgos-y-deudas-tecnicas.md). Con Groq como principal desde ADR-0013, la espera de Gemini solo ocurre cuando Groq ya falló.

## Lo que no está medido

- **S3 de extremo a extremo** (desde que el backend recibe el mensaje hasta que responde por el canal) y **RNF-08** (CRUD). No hay una medición registrada en el repositorio.
- Ambos se observan en producción con `GET https://taia-sistema.iscoutb.dev/metrics` (exige JWT), que devuelve `http_request_duration_p95_ms` por ruta junto a su objetivo. La ventana son las últimas 1 000 peticiones por ruta, en memoria, y **se reinicia con cada despliegue**, así que hay que usar la app un rato antes de consultarla.
- Por tanto, el p95 del modelo es una cota inferior de lo que ve el estudiante: le faltan la base de datos, la red hasta Supabase y el canal.
