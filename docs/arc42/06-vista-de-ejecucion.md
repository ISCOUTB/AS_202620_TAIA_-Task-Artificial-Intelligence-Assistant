# 6. Vista de ejecución

La vista de ejecución describe cómo colaboran los bloques de TAIA en los escenarios con más peso arquitectónico: los que cruzan módulos, llaman a servicios externos, aíslan los datos de cada usuario o manejan fallos. Los nombres de los bloques son los de la [vista de bloques](05-vista-de-bloques-de-construccion.md).

---

## 6.1. Autenticación de una solicitud

Toda ruta exige JWT salvo las excepciones de RT-01 (registro, inicio de sesión, renovación, recuperación de contraseña, webhook de Telegram y salud).

```text
App móvil
   │ Authorization: Bearer <JWT>
   ▼
Ruta de cualquier módulo
   │ CurrentUserId (app/shared/adapters/inbound/auth.py)
   ▼
IdentityService (Usuario)
   ├── token inválido o vencido ──► 401
   ├── cuenta desactivada ────────► 401
   ▼
user_id ──► caso de uso del módulo ──► repositorio filtrado por user_id
```

El `user_id` sale siempre del token, nunca del cuerpo de la petición. Un recurso de otro usuario responde `404` (RT-02).

El inicio de sesión (`POST /users/login`) entrega un JWT de acceso y un token de renovación. `POST /users/refresh` renueva la sesión, y los intentos fallidos de inicio de sesión se limitan por cuenta.

---

## 6.2. Crear una actividad desde la app

```text
App móvil
   │ POST /academic/tasks
   ▼
Academic API ──► manage_tasks (crear)
   │                ├── valida asignatura, fecha y tipo (dominio)
   │                ├── TaskRepository.add (SQLAlchemy)
   │                └── TaskReminderSync.on_task_created ──► Reminders
   │                                                          └── crea los recordatorios
   │                                                              por defecto (RF-REC-02)
   ▼
201 con la actividad
```

Completar, reabrir, cambiar la fecha o eliminar la actividad avisa a Reminders por el mismo puerto (`on_task_closed`, `on_task_reopened`, `on_due_changed`), que cancela o recalcula los recordatorios pendientes (RF-REC-06).

---

## 6.3. Crear una actividad por lenguaje natural, con confirmación

El mismo recorrido sirve para la app (`POST /ai/message`) y para Telegram (`POST /telegram/webhook`).

```text
Estudiante: "tengo parcial de cálculo el viernes a las 10"
   │
   ▼
HandleUserMessageUseCase (AI)
   ├── límite de uso superado ──► 429 (RF-AGT-19)
   ├── contexto acotado de la conversación (RF-AGT-15)
   ▼
FallbackLLM ──► Groq (cada clave) ──► Gemini
   │  el texto del estudiante va delimitado como dato;
   │  el LLM no recibe identificadores de usuario
   ▼
interpretation_contract: valida intención y campos
   ├── confianza baja o intención fuera de la lista ──► pide aclarar
   ▼
Guarda la acción pendiente y pregunta: "¿La registro?"
   │
Estudiante: "sí"
   ▼
Confirmación determinista, sin LLM (RF-AGT-04, ADR-0005)
   ▼
AcademicGateway ──► AcademicTaskManagement (Academic)
   ▼
Se crea la actividad, con sus recordatorios (6.2)
```

En Telegram, la identidad sale de la vinculación de la cuenta (6.5). La respuesta viaja en el cuerpo de la respuesta del webhook, como `method: sendMessage`, así que la API no llama a Telegram.

---

## 6.4. Fallo del proveedor LLM

```text
FallbackLLM
   ├── Groq clave 1 ── error o timeout ──┐
   ├── Groq clave 2 ── error o timeout ──┤
   ├── Gemini ──────── error o timeout ──┤
   ▼                                     │
Todos fallaron ◄─────────────────────────┘
   ▼
El agente responde que no está disponible y no ejecuta nada (RF-AGT-20, ADR-0007)
```

El primer proveedor que responde corta la cadena. Con Groq disponible, una caída de Gemini no se nota ([ADR-0013](../adr/0013-usar-groq-como-proveedor-llm-principal.md)). Las pruebas están en `test_ai_fallback_llm.py`.

---

## 6.5. Vincular la cuenta de Telegram

```text
App móvil
   │ POST /users/me/telegram/link
   ▼
Usuario: genera un código temporal ──► enlace t.me/<bot>?start=<código>

Telegram
   │ update "/start <código>", cabecera X-Telegram-Bot-Api-Secret-Token
   ▼
POST /telegram/webhook
   ├── secreto incorrecto ──► 401
   ▼
ConfirmTelegramLinkUseCase
   ├── código inexistente, vencido o usado ──┐
   ├── Telegram ya vinculado a otra cuenta ──┤──► 204 sin vincular
   ▼                                         │
Guarda telegram_user_id (message.from.id) ──► 204
```

El webhook responde `2xx` incluso cuando rechaza la vinculación, porque Telegram reintenta cualquier otra respuesta (RF-TEL-02). Por eso el bot todavía no le dice al estudiante si la vinculación funcionó: RF-TEL-01 queda *Parcial*.

---

## 6.6. Envío automático de un recordatorio

```text
Bucle de envío (lifespan de la API, cada 60 s, ADR-0012)
   ▼
DispatchDueRemindersUseCase.execute(ahora en America/Bogota)
   │ por cada recordatorio pending con scheduled_at <= ahora:
   ├── cuenta inactiva o actividad cerrada ──► cancela el recordatorio
   ├── claim: UPDATE condicional + notificación ──► si otro proceso ya lo tomó, sigue
   ▼
UserDeviceDirectory (Usuario): tokens FCM del estudiante
   ├── sin tokens o sin FCM configurado ──► queda en la bandeja (RF-NOT-04)
   ▼
FcmPushSender ──► Firebase Cloud Messaging ──► teléfono
   ├── token inválido ──► se borra
   ├── error de FCM ────► hasta 3 reintentos (1, 2 y 4 s), solo a los tokens que fallaron
   ▼
Registra intentos y push_sent_at; una línea de log por recordatorio
```

Un fallo en un recordatorio no detiene a los demás, y un fallo de una vuelta no detiene el bucle. La bandeja (`GET /notifications`) muestra la notificación aunque el push no haya llegado.

---

## 6.7. Manejo transversal de errores

Los casos de uso lanzan errores de aplicación y el adaptador HTTP de cada módulo los traduce al código de RT-05, con el formato `{"detail": "..."}`.

| Situación | Módulo | Resultado |
| --- | --- | --- |
| Credenciales inválidas o JWT inválido | Usuario | `401` |
| Correo ya registrado | Usuario | `409` |
| Recuperación de contraseña sin Resend configurado | Usuario | `503` |
| Recurso inexistente o de otro usuario | Todos | `404` |
| Datos inválidos | Todos | `422` |
| Límite de uso del agente superado | AI | `429` |
| Secreto del webhook incorrecto | Usuario | `401` |

---

## 6.8. Integración de la API principal: contrato HTTP síncrono

La API usa **HTTP síncrono** y **JSON** ([ADR-0002](../adr/0002-estrategia-integracion-api-sincrona.md)). El contrato versionado es [`docs/api/openapi.json`](../api/openapi.json); `test_api_contract.py` comprueba que coincide con la aplicación, y el cliente generado se regenera con `tools/generate_api_client.py`.

```text
App móvil ── HTTPS + JSON + Bearer JWT ──► API TAIA ──► caso de uso ──► respuesta JSON
```

### Flujos de integración externos

```text
API TAIA ── HTTPS + JSON ──► Groq, Gemini       (interpretación)
Telegram ── HTTPS + JSON ──► API TAIA           (webhook; la respuesta va en el cuerpo)
API TAIA ── HTTPS ─────────► Firebase Cloud Messaging (push)
API TAIA ── HTTPS + JSON ──► Resend             (correo de recuperación)
API TAIA ── SQL/TCP 5432 ──► PostgreSQL
```
