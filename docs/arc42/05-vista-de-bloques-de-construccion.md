# 5. Vista de bloques de construcción

## 5.1. Vista general del sistema

TAIA se implementa como un **monolito modular** ([ADR-0001](../adr/0001-estilo-arquitectonico.md), [ADR-0008](../adr/0008-mantener-monolito-sin-extraer-modulos.md)). Los cuatro módulos del backend viven en `backend/app/modules/`:

* **Usuario:** identidad, sesión, perfil, consentimiento, dispositivos y vinculación con Telegram.
* **Academic:** asignaturas, horario, período, actividades (tareas y exámenes), calendario, estadísticas y plan de estudio.
* **Reminders:** recordatorios, su envío automático por FCM y la bandeja de notificaciones.
* **AI:** el agente conversacional, que interpreta mensajes con un LLM y opera sobre Academic.

Cada módulo tiene tres capas. `domain` contiene las entidades y no importa SQLAlchemy. `application` contiene los puertos y los casos de uso. `adapters` contiene la entrada (HTTP, webhook) y la salida (repositorios SQLAlchemy, proveedores externos). Los modelos ORM se convierten a entidades de dominio con *mappers*.

```text
             HTTP / webhook
                   │
                   ▼
        ┌──────────────────────┐
        │ adapters/inbound     │   rutas FastAPI, webhook de Telegram
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ application          │   casos de uso y puertos
        │  ports/inbound  ◄────┼── usados por otros módulos
        │  ports/outbound      │
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ domain               │   entidades y reglas
        └──────────────────────┘
                   ▲
        ┌──────────┴───────────┐
        │ adapters/outbound    │   SQLAlchemy, Groq/Gemini, FCM, Resend
        └──────────────────────┘
```

## 5.2. Bloques de construcción contenidos

### 5.2.1 Módulo Usuario

**Responsabilidad.** Registrar y autenticar al estudiante, mantener la sesión (JWT de acceso y token de renovación), gestionar el perfil, el consentimiento de datos, la desactivación de la cuenta, la recuperación de contraseña, los tokens FCM de los dispositivos y la vinculación con Telegram.

| Bloque | Responsabilidad |
| --- | --- |
| `adapters/inbound/api.py` | Rutas `/users`. |
| `adapters/inbound/telegram_webhook.py` | `POST /telegram/webhook`: vincula con `/start <código>` y pasa los demás mensajes al agente (RF-TEL-04). |
| `register_user`, `login_user`, `manage_sessions` | Registro, inicio de sesión con límite de intentos, renovación y cierre de sesión. |
| `manage_account`, `reset_password` | Perfil, contraseña, desactivación y recuperación por correo. |
| `manage_devices`, `link_telegram` | Tokens FCM y vinculación con Telegram. |
| `IdentityService` (puerto de entrada) | Autentica el JWT para los demás módulos. |
| `UserDeviceDirectory` (puerto de entrada) | Da a Reminders los tokens FCM y si la cuenta está activa. |
| Adaptadores de salida | Repositorios SQLAlchemy, `JwtTokenService`, `Pbkdf2PasswordHasher`, `ResendPasswordResetMailer`. |

### 5.2.2 Módulo Academic

**Responsabilidad.** La información académica del estudiante: asignaturas con alias y archivado, bloques de horario, período académico, actividades con prioridad calculada y estado `overdue`, calendario, estadísticas del perfil y plan de estudio.

| Bloque | Responsabilidad |
| --- | --- |
| `api.py`, `structure_api.py`, `calendar_api.py`, `statistics_api.py`, `study_plan_api.py` | Rutas `/academic/...`. |
| `manage_tasks`, `manage_subjects`, `manage_schedule`, `manage_academic_period` | Casos de uso de actividades, asignaturas, horario y período. |
| `academic_calendar`, `profile_statistics` | Calendario y estadísticas. |
| `manage_study_plan`, `study_planner.py` | Genera, acepta y descarta el plan de estudio (RF-EST-01 a 03). |
| `AcademicTaskManagement`, `AcademicInsights` (puertos de entrada) | Los usan AI y Reminders. |
| `ai_study_session_advisor.py` (adaptador de salida) | Pide a AI el consejo del plan mediante `StudyPlanAdvisor`. |
| Repositorios SQLAlchemy | Tareas, asignaturas, horario, período y plan. |

### 5.2.3 Módulo AI

**Responsabilidad.** El agente conversacional. Recibe el mensaje desde la app o desde Telegram, lo interpreta con el LLM, valida la salida, pide confirmación antes de escribir (RF-AGT-04) y ejecuta la operación mediante los puertos de Academic. El LLM no accede a la persistencia, no recibe identificadores de usuario y ningún identificador que produzca se usa para acceder a datos.

| Bloque | Responsabilidad |
| --- | --- |
| `adapters/inbound/api.py` | `POST /ai/message`. |
| `handle_message.py`, `telegram_chat.py` | Coordinan interpretación, confirmación y ejecución para la app y para Telegram. |
| `advise_study_plan.py` | Publica `StudyPlanAdvisor` para Academic. |
| `LLM` (puerto de salida) | Abstrae el proveedor. |
| `FallbackLLM` | Groq con cada clave configurada y después Gemini; si fallan todos, falla cerrado ([ADR-0013](../adr/0013-usar-groq-como-proveedor-llm-principal.md), [ADR-0007](../adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md)). |
| `GroqLLM`, `GeminiLLM`, `interpretation_contract.py` | Adaptadores de cada proveedor y contrato común: reglas, texto del estudiante delimitado como dato y validación de la salida. |
| `AcademicGateway` | Traduce las operaciones del agente a `AcademicTaskManagement` y `AcademicInsights`. |
| `SqlAlchemyConversationStore` | Contexto conversacional acotado (RF-AGT-15). |

### 5.2.4 Módulo Reminders

**Responsabilidad.** Los recordatorios de cada actividad, por defecto (RF-REC-02) y personalizados, sincronizados con el ciclo de vida de la actividad (RF-REC-06). También el envío automático y la bandeja de notificaciones.

| Bloque | Responsabilidad |
| --- | --- |
| `http_controller.py` | Rutas `/reminders`. |
| `notifications_controller.py` | Rutas `/notifications` (bandeja, no leídas, marcar como leídas). |
| `reminder_dispatch_loop.py` | Proceso asyncio que corre en el *lifespan* de la API y cada 60 s llama al despacho ([ADR-0012](../adr/0012-enviar-recordatorios-con-un-proceso-dentro-de-la-api.md)). |
| `dispatch_due_reminders.py` | Toma cada recordatorio vencido una sola vez (`claim`, un `UPDATE` condicional), crea la notificación y la envía con hasta 3 reintentos. Sin dispositivos o sin FCM, queda en la bandeja (RF-NOT-04). |
| `TaskReminderSync` (puerto de entrada) | Academic y Usuario lo llaman al crear, cambiar, completar o eliminar una actividad y al desactivar la cuenta. |
| `PushSender` / `FcmPushSender` | Envío por Firebase Cloud Messaging. Sin `FIREBASE_CREDENTIALS_JSON` queda desactivado y la API arranca igual. |
| `AcademicTaskLookupAdapter` | Consulta la actividad mediante `AcademicTaskManagement`. |
| Repositorios SQLAlchemy | Recordatorios y notificaciones. |

## 5.3. Integración entre los cuatro módulos

Un módulo nunca importa los adaptadores ni los repositorios de otro: solo los puertos de entrada que publica el módulo propietario. `tools/audit_boundaries.py` lo comprueba en el CI.

```text
                      ┌────────────────────┐
     JWT ────────────►│      Usuario       │◄──── Telegram (webhook)
                      │ IdentityService    │
                      │ UserDeviceDirectory│
                      └──┬──────────────▲──┘
            AgentChat    │              │ UserDeviceDirectory
                         ▼              │
   ┌──────────┐  AcademicTaskManagement ┌──────────────┐
   │    AI    │────────────────────────►│   Academic   │
   │          │◄────────────────────────│              │
   └────┬─────┘     StudyPlanAdvisor    └──┬────────▲──┘
        │                  TaskReminderSync │        │ AcademicTaskManagement
        ▼                                   ▼        │
   Groq -> Gemini                         ┌──────────┴───┐
                                          │  Reminders   │──► FCM
                                          └──────────────┘
```

| Origen | Destino | Puerto |
| --- | --- | --- |
| Academic, AI, Reminders | Usuario | `IdentityService` (autenticación compartida en `app/shared/adapters/inbound/auth.py`) |
| Usuario (webhook) | AI | `AgentChat` |
| AI | Academic | `AcademicTaskManagement`, `AcademicInsights` |
| Academic | AI | `StudyPlanAdvisor` |
| Academic, Usuario | Reminders | `TaskReminderSync` |
| Reminders | Academic | `AcademicTaskManagement` |
| Reminders | Usuario | `UserDeviceDirectory` |

## 5.4. Composición de la aplicación

El punto de composición es `backend/app/main.py`. Crea los repositorios, el proveedor LLM y el emisor FCM, configura los casos de uso, registra los routers y arranca el bucle de recordatorios en el *lifespan*.

```text
FastAPI
 ├── /users, /telegram/webhook        Usuario
 ├── /academic/...                    Academic
 ├── /ai/message                      AI
 ├── /reminders, /notifications       Reminders
 └── /health                          Salud
```

La aplicación es una única unidad desplegable ([arc42 §7](07-vista-de-despliegue.md)). El contrato completo está en [`openapi.json`](../api/openapi.json).

## 5.5. Persistencia

Cada módulo persiste en PostgreSQL con repositorios SQLAlchemy en sus adaptadores de salida, sobre un `Base` compartido en `app/shared/`. Cada tabla tiene un único módulo propietario y no hay claves foráneas entre módulos ([ADR-0009](../adr/0009-base-compartida-con-referencias-logicas-entre-modulos.md), [diccionario de datos](../diccionario_datos.md)). El esquema se versiona con Alembic.

Los repositorios en memoria se conservan para las pruebas unitarias.

## 5.6. Límites actuales de los bloques

Lo implementado y lo pendiente se lleva por requisito en [requerimientos.md](../requerimientos.md). Al cierre quedan como *Pendiente* RF-REC-07 y RF-AGT-21. Las capacidades avanzadas de IA (RAG, embeddings, búsqueda semántica) quedan fuera del MVP.
