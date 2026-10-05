# ADR-0007 — Comportamiento ante fallo o degradación del proveedor de lenguaje

## Estado

Propuesto. Pendiente de ratificación por el equipo.

## Contexto

TAIA interpreta los mensajes del estudiante con un proveedor externo de lenguaje, hoy Gemini (`gemini-3.5-flash-lite`), detrás del puerto `LLMPort` (ver [ADR-0001](0001-estilo-arquitectonico.md)). El proveedor no lo construimos ni lo controlamos (sistema externo en el [C4 nivel 2](../c4/C4-C2.md)), y opera en su nivel gratuito, con límites que ya se observaron en el proyecto:

- **Límite de cadencia.** En la primera corrida de evaluación, nueve errores consecutivos aparecieron cuando las llamadas se hicieron seguidas, y desaparecieron con una pausa de seis segundos entre llamadas ([arc42 §11](../arc42/11-riesgos-y-deudas-tecnicas.md), [ia.md, entrada 014](../ia.md)).
- **Retirada de modelos.** `gemini-2.5-flash` respondió 404 a una credencial nueva (arc42 §11.7).
- **Respuestas malformadas.** El modelo puede devolver un cuerpo sin candidatos, sin texto o con un JSON incompleto si golpea `maxOutputTokens`.

Hasta ahora el código ya reaccionaba a esos casos, pero la decisión no estaba escrita: no había un documento que dijera qué debe ver el estudiante, qué no debe ocurrir nunca y qué se descartó.

Dos restricciones del proyecto acotan la respuesta:

- El contrato HTTP está congelado ([ADR-0002](0002-estrategia-integracion-api-sincrona.md)). En [`openapi.json`](../api/openapi.json), `POST /ai/message` declara solo `200` y `422`.
- Las escrituras sobre información académica solo ocurren después de una confirmación explícita del estudiante, que se resuelve sin el modelo ([ADR-0005](0005-normalizacion-confirmacion-espanol.md)).

## Escenario de calidad relacionado

**S3 — Respuesta del asistente ante un mensaje** (p95 ≤ 7 s) en [escenarios_calidad.md](../calidad/escenarios_calidad.md): ante un proveedor lento o caído, el estudiante debe recibir una respuesta y no un silencio.

**S1 — Registro correcto de información académica:** un proveedor degradado no debe producir registros incorrectos. Ante la duda, no se escribe.

**S5 — Sustitución del modelo de IA:** el manejo del fallo no debe filtrar detalles de Gemini fuera del adaptador, para que un segundo proveedor pueda sustituirlo sin tocar el caso de uso.

## Opciones consideradas

### Opción A — Fallar cerrado con una respuesta fija, sin reintentos

El adaptador traduce cualquier fallo del proveedor a `LLMError`. El caso de uso lo captura y responde con un texto fijo que invita a reintentar. No se reintenta, no se cambia de proveedor y no se escribe nada.

### Opción B — Reintentar con espera exponencial ante 429 y 5xx

Recupera fallos transitorios sin que el estudiante lo note. Pero el fallo más frecuente observado es el límite de llamadas por minuto, y reintentar contra un límite de cadencia consume la misma cuota que lo provocó. Además, cada reintento suma su latencia a la petición original, lo que empuja el p95 de S3 justo en el momento en que el proveedor ya está lento.

### Opción C — Proveedor o modelo de respaldo

Cubriría también una caída larga o la retirada de un modelo, y el puerto `LLMPort` lo permite. Pero exige un segundo adaptador, una segunda credencial y su propia evaluación de exactitud, porque un modelo distinto interpreta distinto y sus resultados no son comparables con los medidos. En [ia.md, entrada 014](../ia.md), el equipo ya descartó escribir un segundo adaptador en este corte.

### Opción D — Interpretación degradada por reglas, sin modelo

Un intérprete por palabras clave mantendría el asistente "funcionando" con el proveedor caído. Pero sería un segundo intérprete que mantener y evaluar, con una exactitud menor que nadie ha medido, y produciría propuestas de escritura peores precisamente cuando nadie lo nota. Va en contra de S1.

### Opción E — Propagar el fallo como `503` al cliente

Es semánticamente honesto, pero `POST /ai/message` no declara `503` en el contrato congelado, de modo que cambiarlo rompería la prueba de contrato y a los clientes generados. Además, en el canal de Telegram un error HTTP no se traduce en ningún mensaje para el estudiante.

## Decisión

Se adopta la **Opción A**: ante un fallo del proveedor, TAIA **falla cerrado**, responde con un mensaje fijo y no escribe nada.

El comportamiento queda repartido así:

1. **Adaptador (`GeminiLLM`).** Es la única pieza que conoce a Gemini, y actúa como capa anticorrupción. Traduce a `LLMError`:
   - los errores de transporte de `httpx`, incluido el timeout de 20 s (`_DEFAULT_TIMEOUT`);
   - cualquier respuesta no exitosa (`429`, `404`, `5xx`);
   - un cuerpo que no es JSON, una respuesta sin candidatos, sin contenido o sin texto, y un JSON de interpretación inválido.

   Ningún tipo de error de `httpx` ni de Gemini cruza el puerto.
2. **Caso de uso (`HandleUserMessageUseCase`).** Captura `LLMError` en la interpretación y en las dudas sobre el sistema, y responde `replies.service_unavailable()`: «Ahora no puedo procesar tu mensaje. Intenta de nuevo en un momento.» La petición HTTP termina en `200`, con el contrato intacto.
3. **Escrituras.** Un fallo del proveedor nunca crea ni modifica tareas, porque la escritura solo ocurre en `_execute`, después de una confirmación. La confirmación se resuelve sin llamar al modelo, así que una acción que quedó pendiente antes de la caída **se puede confirmar o cancelar durante la caída**: la degradación es parcial, no total.
4. **Sin reintentos automáticos ni respaldo.** El reintento lo decide el estudiante.
5. **Credencial ausente: no se arranca.** Que falte `GEMINI_API_KEY` no es una degradación del proveedor sino un error de configuración. `main.py` construye el adaptador al arrancar y el proceso se detiene, en lugar de responder un fallo en cada petición.
6. **Salud.** `/health` comprueba PostgreSQL pero no llama a Gemini, para no gastar cuota ni dinero en cada sondeo. Un proveedor caído deja al asistente degradado, pero no marca el servicio como no sano: el resto de la API sigue atendiendo.

## Consecuencias

### Positivas

- El estudiante siempre recibe una respuesta comprensible, y el contrato HTTP no cambia.
- Un proveedor degradado no puede producir registros incorrectos: S1 se protege fallando cerrado.
- No se gasta cuota extra en reintentos contra un límite de cadencia.
- Sustituir el proveedor solo exige que el nuevo adaptador traduzca sus fallos a `LLMError`: el caso de uso no cambia (S5).
- El comportamiento es verificable sin red: las pruebas usan `FakeLLM` y `httpx.MockTransport`.

### Negativas

- **El timeout de 20 s supera el umbral de S3 (7 s).** Si el proveedor se cuelga sin responder, el estudiante espera hasta 20 s antes de ver el mensaje de fallo. Sobre el tramo del modelo, el p95 medido es 1 618,8 ms ([resultado_s1_s3.json](../evaluacion_ia/resultado_s1_s3.json)), así que el timeout solo afecta a la cola. Aun así, ajustarlo por debajo de 7 s queda como revisión pendiente de esta decisión.
- **El mensaje no distingue causas.** Un `429` (esperar unos segundos), un `404` (modelo retirado, requiere intervención) y una caída se ven igual para el estudiante.
- **El fallo no queda registrado.** El caso de uso captura `LLMError` sin escribir en el log, y el adaptador solo conserva el tipo del error de transporte. Diagnosticar una degradación en el despliegue exige hoy reproducirla (arc42 §11.6).
- **El registro de consumo puede repetirse tras un fallo.** `GeminiLLM.last_usage()` solo se actualiza cuando la llamada tiene éxito, así que tras un `LLMError` el adaptador HTTP vuelve a registrar el consumo de la llamada anterior como si fuera de esta petición. Eso distorsiona la estimación de costo por operación a partir de los logs.
- Sin respaldo, una caída prolongada o la retirada del modelo dejan al asistente sin interpretar mensajes hasta que se cambie `GEMINI_MODEL` o se despliegue otro adaptador.

## Verificación

- `backend/tests/test_ai_gemini_llm.py`: un `429` (`test_http_error_status_raises_llm_error`), un fallo de red (`test_network_failure_raises_llm_error`), una respuesta sin candidatos, un contenido que no es JSON y una respuesta de ayuda vacía producen `LLMError`. Ninguna prueba sale a la red.
- `backend/tests/test_ai_handle_message.py::test_llm_failure_returns_friendly_message`: con el proveedor fallando, el caso de uso responde el mensaje de reintento.
- `backend/tests/test_ai_create_task_confirmation.py`: la confirmación de una acción pendiente se resuelve sin llamar al modelo.
- Las negativas anteriores no tienen prueba que las cubra. Son deuda registrada, no comportamiento verificado.
