# Modos de fallo de las integraciones externas (S11)

Este documento analiza qué pasa en TAIA cuando el otro lado de una integración no responde,
responde tarde o la operación llega dos veces, y qué hace el sistema en cada caso. Cada
mitigación cita el código que la implementa o se declara pendiente con su plan.

La decisión de fondo sobre el proveedor de lenguaje está en
[ADR-0007](adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md); aquí se ordena por modo de
fallo y se contrasta con el código y las pruebas.

## Integración principal: Gemini

TAIA interpreta cada mensaje del estudiante con una llamada HTTP síncrona a la API REST de Gemini.
Es la única llamada de red en el camino de una petición del asistente (`POST /ai/message`).

| Pieza | Ruta |
|---|---|
| Cliente HTTP y timeout de 20 s | [`gemini_llm.py:32`](../backend/app/modules/ai/adapters/outbound/gemini_llm.py) (`_DEFAULT_TIMEOUT`), [`gemini_llm.py:93`](../backend/app/modules/ai/adapters/outbound/gemini_llm.py) (`httpx.Client(timeout=...)`) |
| Llamada y traducción de errores a `LLMError` | [`gemini_llm.py:138-164`](../backend/app/modules/ai/adapters/outbound/gemini_llm.py) (`_generate`) |
| Validación de la forma de la respuesta | [`gemini_llm.py:173-187`](../backend/app/modules/ai/adapters/outbound/gemini_llm.py) (`_extract_text`), [`gemini_llm.py:226`](../backend/app/modules/ai/adapters/outbound/gemini_llm.py) (`_load_json`) |
| Captura de `LLMError` y mensaje al estudiante | [`handle_message.py:100-101`](../backend/app/modules/ai/application/use_cases/handle_message.py), [`replies.py:99`](../backend/app/modules/ai/application/replies.py) (`service_unavailable`) |
| Escritura solo tras confirmación, resuelta sin el modelo | [`handle_message.py:191-217`](../backend/app/modules/ai/application/use_cases/handle_message.py) (`_resolve_pending`, `_execute`) |

Requisitos relacionados: `RF-AGT-20` (degradación si el LLM no está disponible), `RF-AGT-04`
(confirmación determinista) y `RNF-09` (una caída de Gemini no impide usar el resto de funciones).

### Tabla de modos de fallo

| Modo de fallo | Causa típica | Efecto para el estudiante | Mitigación | Dónde está en el código | Estado | Prueba |
|---|---|---|---|---|---|---|
| **No responde** | Error de red, DNS, conexión rechazada o respuesta `5xx` | Recibe «Ahora no puedo procesar tu mensaje. Intenta de nuevo en un momento.» No se crea ni se modifica nada. | Fallar cerrado: el adaptador traduce el fallo a `LLMError` y el caso de uso responde un mensaje fijo, sin reintentos (ADR-0007, opción A). | `gemini_llm.py:152` (error de transporte), `gemini_llm.py:155` (estado no exitoso), `handle_message.py:100-101` | Implementada | [`test_network_failure_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py), [`test_http_error_status_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py), [`test_llm_failure_returns_friendly_message`](../backend/tests/test_ai_handle_message.py) |
| **Responde tarde** | Proveedor saturado o colgado | Espera hasta 20 s y recibe el mismo mensaje fijo. | Timeout de 20 s en el cliente `httpx`; al vencer, `httpx.ReadTimeout` se traduce a `LLMError` por la misma ruta que "no responde". | `gemini_llm.py:32`, `gemini_llm.py:93`, `gemini_llm.py:152` | Implementada, con una negativa declarada: 20 s supera el umbral de S3 (p95 ≤ 7 s). El p95 medido del modelo es 1 618,8 ms, así que el timeout solo afecta a la cola. ADR-0007 acepta el riesgo con el valor actual. | Pendiente: no hay prueba que simule el timeout. |
| **Llega dos veces** | El estudiante envía «sí» dos veces o el cliente reintenta `POST /ai/message` | Si los dos «sí» llegan **seguidos**, se crea una sola tarea: el primero consume la acción pendiente y el segundo ya no la encuentra. Si llegan **a la vez**, se pueden crear **dos tareas**. | Secuencial: la acción pendiente se borra antes de ejecutarse. Concurrente: ninguna; la conversación se lee al empezar y se guarda al final sin bloqueo. | `handle_message.py:81` (lectura), `handle_message.py:196-199` (consumo de la acción), `handle_message.py:87` (guardado) | Secuencial: implementada. Concurrente: pendiente; el diseño está en la sección [Idempotencia y transacciones](#idempotencia-y-transacciones). | Pendiente: no hay prueba de la confirmación repetida. |
| Límite de cadencia (`429`) | Ráfaga de llamadas contra la cuota por minuto del nivel gratuito | Mismo mensaje fijo; el estudiante decide cuándo reintentar. | `LLMError` sin reintento automático: reintentar contra un límite de cadencia consume la misma cuota que lo provocó (ADR-0007, opción B descartada). | `gemini_llm.py:155` | Implementada | [`test_http_error_status_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py) (simula un `429`) |
| Respuesta malformada | Cuerpo que no es JSON, sin candidatos, sin texto, o JSON cortado por `maxOutputTokens` | Mismo mensaje fijo; no se escribe nada. | Validación estricta de la forma de la respuesta en la capa anticorrupción; cualquier desviación es `LLMError`. | `gemini_llm.py:161`, `gemini_llm.py:173-187`, `gemini_llm.py:226` | Implementada | [`test_response_without_candidates_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py), [`test_non_json_content_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py), [`test_answer_system_help_rejects_empty_answer`](../backend/tests/test_ai_gemini_llm.py) |
| Modelo retirado (`404`) | Google retira el modelo configurado | Mismo mensaje fijo hasta que se cambie `GEMINI_MODEL` y se reinicie. | `LLMError`; la recuperación es manual ([arc42 §11.7](arc42/11-riesgos-y-deudas-tecnicas.md)). | `gemini_llm.py:155` | Implementada (sin recuperación automática) | Cubierta por la misma ruta que el `429` |

### Comportamiento durante la caída

La degradación es parcial, no total:

- Una acción que quedó pendiente antes de la caída se puede confirmar o cancelar durante la caída,
  porque la confirmación se resuelve sin llamar al modelo (`RF-AGT-04`). Prueba:
  [`test_ai_create_task_confirmation.py`](../backend/tests/test_ai_create_task_confirmation.py).
- El resto de la API (tareas, recordatorios, usuarios) no depende de Gemini y sigue atendiendo
  (`RNF-09`). `/health` comprueba PostgreSQL y no llama a Gemini.

## Integración secundaria: Telegram (envío de notificaciones)

El envío de una notificación llama a `sendMessage` de la API de Telegram.

| Pieza | Ruta |
|---|---|
| Cliente HTTP y timeout de 5 s | [`telegram_bot_client.py:11`](../backend/app/modules/reminders/adapters/outbound/telegram_bot_client.py), [`telegram_bot_client.py:28-31`](../backend/app/modules/reminders/adapters/outbound/telegram_bot_client.py) |
| El adaptador convierte cualquier fallo en `False` | [`telegram_notification_sender.py:23-36`](../backend/app/modules/reminders/adapters/outbound/telegram_notification_sender.py) |
| Envío y registro del intento | [`send_notification.py`](../backend/app/modules/reminders/application/use_cases/send_notification.py), [`sqlalchemy_reminder_repository.py:91-105`](../backend/app/modules/reminders/adapters/outbound/sqlalchemy_reminder_repository.py) |
| Respuesta `503` al cliente | [`http_controller.py:170-198`](../backend/app/modules/reminders/adapters/inbound/http_controller.py) (`POST /reminders/{id}/notify`) |

| Modo de fallo | Efecto | Mitigación | Dónde está en el código | Estado | Prueba |
|---|---|---|---|---|---|
| **No responde** | `POST /reminders/{id}/notify` responde `503`; se registra el intento sin `push_sent_at`. | El error de `urllib` se traduce a `RuntimeError` y el adaptador devuelve `False`. | `telegram_bot_client.py:30-31`, `telegram_notification_sender.py:34-35`, `http_controller.py:191-198` | Implementada | [`test_telegram_sender_returns_false_when_user_has_no_telegram`](../backend/tests/test_reminders_notifications.py) cubre el camino de `False`; no hay prueba con la red caída. |
| **Responde tarde** | Igual que "no responde" a los 5 s. | Timeout de 5 s en `urlopen`. | `telegram_bot_client.py:11`, `telegram_bot_client.py:28` | Implementada | Pendiente |
| **Llega dos veces** | Si Telegram entregó el mensaje pero la respuesta se perdió por el timeout, un nuevo `POST .../notify` lo vuelve a enviar: el estudiante recibe el recordatorio duplicado. | Ninguna: el caso de uso envía sin comprobar `push_sent_at`. | `send_notification.py` | Pendiente; el diseño está en la sección [Idempotencia y transacciones](#idempotencia-y-transacciones). | Pendiente |

## Tácticas de la semana y su estado en TAIA

| Táctica | Estado | Motivo o plan |
|---|---|---|
| Timeout | Implementada | 20 s hacia Gemini y 5 s hacia Telegram (rutas en las tablas anteriores). |
| Reintentos con espera creciente | No implementada, por decisión | ADR-0007, opción B: el fallo más frecuente es el límite de cadencia, y reintentar consume la misma cuota y suma latencia a S3. El reintento lo decide el estudiante. |
| Circuit breaker | No implementado | Hay un solo proveedor y ningún respaldo al que conmutar; ante un fallo rápido (`429`, `5xx`) la llamada ya termina sin esperar. Abrir el circuito solo ahorraría la espera del timeout en una caída prolongada. Se revisa si se agrega un proveedor de respaldo (ADR-0007, opción C). |
| Idempotencia | Parcial | Ver la sección [Idempotencia y transacciones](#idempotencia-y-transacciones). |
| Saga y outbox | No aplica hoy | Ver la sección [Idempotencia y transacciones](#idempotencia-y-transacciones). La mensajería es tema de la semana 12. |

## Qué está probado y qué solo está descrito

| Modo de fallo | Probado | Solo descrito |
|---|---|---|
| Gemini no responde | Sí | |
| Gemini responde tarde | | Sí |
| Gemini: confirmación repetida | | Sí |
| Gemini: `429`, respuesta malformada | Sí | |
| Telegram no responde o responde tarde | | Sí |
| Telegram: envío duplicado | | Sí |

## Idempotencia y transacciones

Pendiente de redactar.
