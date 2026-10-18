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
| Captura de `LLMError` y mensaje al estudiante | [`handle_message.py:105-106`](../backend/app/modules/ai/application/use_cases/handle_message.py), [`replies.py:99`](../backend/app/modules/ai/application/replies.py) (`service_unavailable`) |
| Escritura solo tras confirmación, resuelta sin el modelo | [`handle_message.py:95-101`](../backend/app/modules/ai/application/use_cases/handle_message.py) (reclamo de la acción), [`handle_message.py:196-220`](../backend/app/modules/ai/application/use_cases/handle_message.py) (`_resolve_pending`, `_execute`) |

Requisitos relacionados: `RF-AGT-20` (degradación si el LLM no está disponible), `RF-AGT-04`
(confirmación determinista) y `RNF-09` (una caída de Gemini no impide usar el resto de funciones).

### Tabla de modos de fallo

| Modo de fallo | Causa típica | Efecto para el estudiante | Mitigación | Dónde está en el código | Estado | Prueba |
|---|---|---|---|---|---|---|
| **No responde** | Error de red, DNS, conexión rechazada o respuesta `5xx` | Recibe «Ahora no puedo procesar tu mensaje. Intenta de nuevo en un momento.» No se crea ni se modifica nada. | Fallar cerrado: el adaptador traduce el fallo a `LLMError` y el caso de uso responde un mensaje fijo, sin reintentos (ADR-0007, opción A). | `gemini_llm.py:152` (error de transporte), `gemini_llm.py:155` (estado no exitoso), `handle_message.py:105-106` | Implementada | [`test_network_failure_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py), [`test_http_error_status_raises_llm_error`](../backend/tests/test_ai_gemini_llm.py), [`test_llm_failure_returns_friendly_message`](../backend/tests/test_ai_handle_message.py) |
| **Responde tarde** | Proveedor saturado o colgado | Espera hasta 20 s y recibe el mismo mensaje fijo. | Timeout de 20 s en el cliente `httpx`; al vencer, `httpx.ReadTimeout` se traduce a `LLMError` por la misma ruta que "no responde". | `gemini_llm.py:32`, `gemini_llm.py:93`, `gemini_llm.py:152` | Implementada, con una negativa declarada: 20 s supera el umbral de S3 (p95 ≤ 7 s). El p95 medido del modelo es 1 618,8 ms, así que el timeout solo afecta a la cola. ADR-0007 acepta el riesgo con el valor actual. | [`test_timeout_raises_llm_error_rf_agt_20`](../backend/tests/test_ai_gemini_llm.py), [`test_default_client_timeout_is_twenty_seconds_rf_agt_20`](../backend/tests/test_ai_gemini_llm.py), [`test_gemini_timeout_returns_friendly_message_without_writing_rf_agt_20`](../backend/tests/test_ai_handle_message.py) |
| **Llega dos veces** | El estudiante envía «sí» dos veces o el cliente reintenta `POST /ai/message` | Se crea una sola tarea, lleguen los dos «sí» seguidos o a la vez. La petición que pierde se atiende como un mensaje sin acción pendiente. | Reclamo atómico de la acción antes de ejecutarla: solo la petición que la reclama la ejecuta ([diseño](#confirmación-de-una-acción-pendiente)). | `handle_message.py:95-101` (reclamo), `sqlalchemy_conversation_store.py:54-75` (`take_pending` con `SELECT ... FOR UPDATE`) | Implementada | Seguidos: [`test_confirmacion_repetida_crea_una_sola_tarea_rf_agt_04`](../backend/tests/test_ai_create_task_confirmation.py). Simultáneos: [`test_confirmaciones_simultaneas_crean_una_sola_tarea_rf_agt_04`](../backend/tests/test_ai_create_task_confirmation.py) y, con PostgreSQL y ocho hilos, [`test_take_pending_hands_the_action_to_a_single_caller_rf_agt_04`](../backend/tests/test_sql_persistence_replacements.py). |
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
| Idempotencia | Implementada en la confirmación; pendiente en el envío de notificaciones | Ver la sección [Idempotencia y transacciones](#idempotencia-y-transacciones). |
| Saga y outbox | No aplica hoy | Ver la sección [Idempotencia y transacciones](#idempotencia-y-transacciones). La mensajería es tema de la semana 12. |

## Qué está probado y qué solo está descrito

| Modo de fallo | Probado | Solo descrito |
|---|---|---|
| Gemini no responde | Sí | |
| Gemini responde tarde | Sí | |
| Gemini: confirmación repetida, secuencial | Sí | |
| Gemini: confirmación repetida, concurrente | Sí | |
| Gemini: `429`, respuesta malformada | Sí | |
| Telegram no responde o responde tarde | | Sí |
| Telegram: envío duplicado | | Sí |

## Idempotencia y transacciones

Una operación es idempotente si repetirla produce el mismo efecto que ejecutarla una vez. En TAIA
hay dos operaciones de escritura que pueden llegar repetidas: la confirmación de una acción
pendiente y el envío de una notificación.

### Confirmación de una acción pendiente

**Problema.** Antes de este cambio (commit `354fd0e`), el caso de uso leía la conversación al
empezar (`handle_message.py:81`), borraba la acción pendiente en memoria y la ejecutaba
(`handle_message.py:196-199`), y guardaba la conversación al final (`handle_message.py:87`). La
lectura y el guardado usan sesiones distintas, y la tarea se crea en una tercera sesión del módulo
`academic` ([`sqlalchemy_task_repository.py:21-22`](../backend/app/modules/academic/adapters/outbound/sqlalchemy_task_repository.py)).
Si dos «sí» llegaban a la vez, ambos leían la acción antes de que alguno guardara, y ambos creaban
la tarea. La prueba `test_confirmaciones_simultaneas_crean_una_sola_tarea_rf_agt_04` lo reprodujo
sobre ese código: **dos tareas** en lugar de una.

**Diseño: reclamar la acción de forma atómica antes de ejecutarla.** El puerto `ConversationStore`
publica `take_pending`, que retira la acción pendiente vigente y la devuelve, o devuelve `None` si
no hay. El caso de uso solo ejecuta la acción que recibió de `take_pending`
([`handle_message.py:95-101`](../backend/app/modules/ai/application/use_cases/handle_message.py)); la petición que recibe `None` se atiende como un mensaje sin
acción pendiente, igual que un segundo «sí» que llega después del primero.

En PostgreSQL, `take_pending` lee y vacía la acción en **una sola transacción corta**
([`sqlalchemy_conversation_store.py:54-75`](../backend/app/modules/ai/adapters/outbound/sqlalchemy_conversation_store.py)):

```sql
SELECT ... FROM conversations
WHERE user_id = :user_id
  AND pending_action IS NOT NULL
  AND pending_action_expires_at > :ahora
FOR UPDATE;
-- si hay fila: se convierte a PendingAction y se ponen a NULL
-- pending_action y pending_action_expires_at; COMMIT.
```

**Por qué funciona.** En el nivel de aislamiento por defecto de PostgreSQL (Read Committed), si un
`SELECT FOR UPDATE` encuentra una fila que otra transacción está modificando, espera a que esa
transacción termine, vuelve a evaluar el `WHERE` sobre la versión nueva de la fila y solo la
devuelve si la sigue cumpliendo
([documentación de PostgreSQL, §13.2.1](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-READ-COMMITTED)).
La segunda petición encuentra `pending_action IS NULL` y no recibe nada. Solo una petición obtiene
la acción.

El bloqueo dura solo lo que tarda el reclamo, no la petición entera: no espera al modelo ni abarca
la escritura en `academic`. Es la misma idea que el diccionario fija para tomar recordatorios
([`diccionario_datos.md`, §7.1, reglas](diccionario_datos.md)): una toma condicionada al estado
que, si no encuentra la fila, significa que otro proceso ya la tomó.

**Alternativas descartadas.**

| Alternativa | Por qué no |
|---|---|
| `UPDATE ... RETURNING` en una sola sentencia | En un `UPDATE`, `RETURNING` devuelve el contenido **nuevo** de la fila, que aquí sería `NULL`. Devolver el anterior con `old.` solo existe desde PostgreSQL 18 ([documentación 17](https://www.postgresql.org/docs/17/dml-returning.html) frente a [la actual](https://www.postgresql.org/docs/current/dml-returning.html)), y la versión de la base desplegada no está verificada. |
| Bloquear la conversación durante toda la petición | Exigiría una transacción que abarque la lectura, la escritura en `academic` y el guardado, lo que cruza la frontera entre módulos ([ADR-0001](adr/0001-estilo-arquitectonico.md)) y mantiene el bloqueo mientras se espera al modelo. |
| Número de versión en `conversations` (bloqueo optimista) | El conflicto se detectaría en `save()`, al final de la petición, cuando la tarea duplicada ya se creó en `academic`. |

**Costo aceptado.** Si la escritura en `academic` falla después de reclamar la acción, la acción ya
no existe y el estudiante tiene que repetir su mensaje. Es fallar cerrado, coherente con S1 y con
[ADR-0007](adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md): ante la duda, no se escribe.

**Cambios.** El método `take_pending` en el puerto
([`conversation_store.py`](../backend/app/modules/ai/application/ports/conversation_store.py)),
implementado en `SqlAlchemyConversationStore` y en
[`InMemoryConversationStore`](../backend/app/modules/ai/adapters/outbound/in_memory_conversation_store.py),
y su uso en el caso de uso. No cambia el esquema ni requiere migración: las columnas
`pending_action` y `pending_action_expires_at` ya existían ([`diccionario_datos.md`, §8.1](diccionario_datos.md)).

**Pruebas** (`RF-AGT-04`):

- [`test_confirmaciones_simultaneas_crean_una_sola_tarea_rf_agt_04`](../backend/tests/test_ai_create_task_confirmation.py):
  dos peticiones que leyeron la conversación con la acción pendiente crean una sola tarea.
- [`test_take_pending_hands_the_action_to_a_single_caller_rf_agt_04`](../backend/tests/test_sql_persistence_replacements.py):
  ocho hilos reclaman la misma acción en PostgreSQL y solo uno la recibe. La prueba ensancha la
  ventana entre la lectura y el borrado; sin `FOR UPDATE` falla en cada corrida.
- [`test_take_pending_ignores_an_expired_action_rf_agt_04`](../backend/tests/test_sql_persistence_replacements.py):
  una acción vencida no se puede reclamar.

**Estado.** Implementada.

### Envío de una notificación

**Problema.** Crear la notificación ya es idempotente: `create_notification` bloquea el recordatorio
y, si la notificación existe, devuelve la existente en lugar de crear otra
([`sqlalchemy_reminder_repository.py:63-85`](../backend/app/modules/reminders/adapters/outbound/sqlalchemy_reminder_repository.py)),
y la tabla tiene `UNIQUE (reminder_id)` ([`diccionario_datos.md`, §7.2](diccionario_datos.md)).
Pero **enviarla no lo es**: `SendNotificationUseCase` llama a Telegram cada vez
([`send_notification.py`](../backend/app/modules/reminders/application/use_cases/send_notification.py)).
El código escribe `push_sent_at` tras un envío exitoso
([`sqlalchemy_reminder_repository.py:101-102`](../backend/app/modules/reminders/adapters/outbound/sqlalchemy_reminder_repository.py)),
pero no lo lee antes de enviar. Un segundo `POST /reminders/{id}/notify` reenvía el mensaje.

**Diseño: aplicar lo que ya fijan el diccionario y `RF-NOT-02`.** `RF-NOT-02` exige que cada
recordatorio genere como máximo una notificación aunque el proceso se ejecute dos veces, y el
diccionario fija que solo se reintentan las notificaciones con `push_sent_at IS NULL` y entre 1 y 3
intentos ([`diccionario_datos.md`, §7.2](diccionario_datos.md)). En el código:

1. Si la notificación ya tiene `push_sent_at`, no se vuelve a enviar y se responde como enviada.
2. Si no lo tiene y `push_attempts` es menor que 4, se envía y se registra el intento.

**Límite declarado: al menos una vez.** Si Telegram entrega el mensaje pero la respuesta se pierde
(por ejemplo, por el timeout de 5 s), TAIA no puede saber que se entregó, y el reintento lo duplica.
`sendMessage` no tiene ningún parámetro de idempotencia o deduplicación
([API de bots de Telegram, `sendMessage`](https://core.telegram.org/bots/api#sendmessage)). Se
acepta: un recordatorio duplicado molesta, pero no corrompe datos, y los intentos están acotados a 4.

**Estado.** Pendiente de implementar.

### Operaciones que ya son idempotentes

| Operación | Mecanismo | Prueba |
|---|---|---|
| Completar una tarea | Conserva el primer `completed_at` (`RF-TAR-07`). | [`test_complete_is_idempotent_and_keeps_first_completed_at_rf_tar_07`](../backend/tests/test_academic_task_domain.py) |
| Crear la notificación de un recordatorio | Bloqueo del recordatorio y `UNIQUE (reminder_id)`. | Sin prueba específica de repetición. |
| Consultas (tareas, recordatorios, historial) | Son lecturas: repetirlas no cambia nada. | |

### Por qué no aplica una saga

Una saga coordina una transacción repartida entre servicios con bases de datos propias: cada paso es
una transacción local y, si uno falla, se compensan los anteriores. En TAIA no existe esa situación:

- **Un proceso y una base de datos.** Todos los módulos corren en el mismo proceso y escriben en la
  misma base PostgreSQL ([ADR-0001](adr/0001-estilo-arquitectonico.md),
  [ADR-0004](adr/0004-plataforma-base-de-datos.md)).
- **La llamada externa es de solo lectura y ocurre antes de escribir.** Gemini solo interpreta el
  mensaje; la escritura ocurre después, en `_execute`, tras la confirmación, y no vuelve a llamar al
  modelo ([`handle_message.py:207-220`](../backend/app/modules/ai/application/use_cases/handle_message.py)).
  Si Gemini falla, no hay nada escrito que compensar.
- **Cada escritura es una transacción local** de un solo módulo, como crear una tarea en `academic`.

Una saga sí haría falta si el módulo `ai` se extrajera a un servicio propio: confirmar y crear la
tarea pasaría a ser una llamada por red del servicio de IA a `academic`, con la posibilidad de que la
tarea se cree y la respuesta se pierda. En ese caso se necesitaría, como mínimo, una clave de
idempotencia en la creación de tareas o un outbox. La mensajería y el outbox se tratan en la
semana 12.
