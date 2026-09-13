# 5. Vista de bloques de construcción

## 5.1. Vista general del sistema

TAIA se implementa actualmente como un **monolito modular**. Los cuatro módulos principales del backend son:

* **Usuario:** identidad, autenticación, autorización y vinculación con Telegram.
* **Academic:** gestión de información académica, actualmente centrada en tareas.
* **AI:** procesamiento de mensajes mediante un LLM y coordinación de operaciones académicas.
* **Reminders:** creación, consulta, edición, finalización y envío de recordatorios asociados a tareas académicas.

Cada módulo organiza sus responsabilidades en capas de entrada, aplicación, dominio y adaptadores cuando existe una dependencia externa o un puerto que deba aislarse.

### Ejemplo vista general Módulo Academic

```text
                         API TAIA
                            │
                            ▼
                  ┌───────────────────┐
                  │ Módulo Academic   │
                  │                   │
                  │ ┌───────────────┐ │
                  │ │   Adapters    │ │
                  │ │    / API      │ │
                  │ └───────┬───────┘ │
                  │         │         │
                  │         ▼         │
                  │ ┌───────────────┐ │
                  │ │ Application   │ │
                  │ │ Use Cases     │ │
                  │ └───────┬───────┘ │
                  │         │         │
                  │         ▼         │
                  │ ┌───────────────┐ │
                  │ │    Domain     │ │
                  │ │     Task      │ │
                  │ └───────┬───────┘ │
                  │         │         │
                  │         ▼         │
                  │ ┌───────────────┐ │
                  │ │ Repository    │ │
                  │ │     Port      │ │
                  │ └───────┬───────┘ │
                  └──────────┼────────┘
                             │
                             ▼
                  InMemoryTaskRepository
```

### Motivation

La separación permite que el caso de uso de registro de tareas dependa de una abstracción de persistencia y no de una implementación concreta.

Esto permite que el adaptador utilizado actualmente en memoria pueda ser reemplazado posteriormente por un adaptador para PostgreSQL sin modificar las reglas principales del dominio.

La estructura busca que las reglas principales permanezcan dentro de los módulos y que las dependencias externas se conecten mediante adaptadores.

## 5.2. Bloques de construcción contenidos

### 5.2.1 Módulo Usuario

### Responsabilidad

El módulo **Usuario** administra la identidad de los estudiantes y proporciona el contexto de autenticación utilizado por los demás módulos.

Sus responsabilidades principales son:

* Registrar usuarios.
* Validar credenciales.
* Generar y validar tokens JWT.
* Obtener el usuario autenticado.
* Proporcionar el identificador del usuario a otros módulos mediante una dependencia de autenticación.
* Generar enlaces temporales para vincular una cuenta de Telegram.
* Confirmar la vinculación de Telegram.
* Evitar que una cuenta de Telegram sea vinculada a más de un usuario.

### Estructura

```text
Usuario
│
├── adapters/
│   ├── inbound/
│   │   └── api.py
│   │
│   └── outbound/
│       ├── in_memory_user_repository.py
│       ├── in_memory_telegram_link_repository.py
│       ├── jwt_token_service.py
│       └── pbkdf2_password_hasher.py
│
├── application/
│   ├── ports/
│   └── use_cases/
│       ├── register_user.py
│       ├── login_user.py
│       ├── get_current_user.py
│       └── link_telegram.py
│
└── domain/
    ├── entities/
    │   └── usuario.py
    └── value_objects/
        └── email.py
```

### Bloques principales

| Bloque                           | Responsabilidad                                                        |
| -------------------------------- | ---------------------------------------------------------------------- |
| `Usuario API`                    | Expone las operaciones HTTP relacionadas con usuarios y autenticación. |
| `RegisterUserUseCase`            | Registra un nuevo usuario y valida que el correo no esté registrado.   |
| `LoginUserUseCase`               | Valida credenciales y genera el JWT.                                   |
| `GetCurrentUserUseCase`          | Recupera el usuario asociado al token autenticado.                     |
| `CreateTelegramLinkUseCase`      | Genera un token temporal para vincular Telegram.                       |
| `ConfirmTelegramLinkUseCase`     | Valida el token y asocia el `telegram_user_id` al usuario.             |
| `Usuario`                        | Entidad de dominio que representa al estudiante.                       |
| `Email`                          | Value Object utilizado para representar y validar el correo.           |
| `UserRepository`                 | Puerto utilizado para abstraer la persistencia de usuarios.            |
| `TelegramLinkRepository`         | Puerto para almacenar tokens temporales de vinculación.                |
| `JwtTokenService`                | Adaptador encargado de crear y validar tokens JWT.                     |
| `Pbkdf2PasswordHasher`           | Adaptador encargado del hash y verificación de contraseñas.            |
| `InMemoryUserRepository`         | Persistencia temporal utilizada en el corte actual.                    |
| `InMemoryTelegramLinkRepository` | Persistencia temporal de los tokens de vinculación.                    |

### Interfaz utilizada por otros módulos

El módulo expone la dependencia:

```text
get_authenticated_user_id()
```

Esta dependencia permite que Academic, AI y Reminders obtengan el `UUID` del usuario autenticado sin depender directamente de la entidad `Usuario`.

Esto mantiene el aislamiento entre contextos y permite que cada módulo aplique sus propias reglas de autorización.

---

### 5.2.2 Módulo Academic

### Responsabilidad

El módulo **Academic** administra la información académica que pertenece al estudiante.

En el estado actual, el principal agregado gestionado es `Task`.

Sus operaciones implementadas son:

* Registrar una tarea.
* Consultar las tareas del usuario.
* Actualizar una tarea.
* Marcar una tarea como completada.

### Estructura

```text
Academic
│
├── adapters/
│   ├── inbound/
│   │   └── api.py
│   │
│   └── outbound/
│       ├── in_memory_task_repository.py
│       └── repository_provider.py
│
├── application/
│   ├── ports/
│   │
│   └── use_cases/
│       ├── register_task.py
│       ├── list_tasks.py
│       ├── update_task.py
│       └── complete_task.py
│
└── domain/
    └── entities/
        └── task.py
```

### Bloques principales

| Bloque                   | Responsabilidad                                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `Academic API`           | Recibe solicitudes HTTP relacionadas con tareas.                                                                             |
| `RegisterTaskUseCase`    | Registra una nueva tarea para el usuario autenticado.                                                                        |
| `ListTasksUseCase`       | Recupera únicamente las tareas pertenecientes al usuario autenticado.                                                        |
| `UpdateTaskUseCase`      | Actualiza los datos permitidos de una tarea.                                                                                 |
| `CompleteTaskUseCase`    | Cambia el estado de una tarea a completada.                                                                                  |
| `Task`                   | Entidad de dominio que representa una tarea académica.                                                                       |
| `TaskRepository`         | Puerto de persistencia utilizado por los casos de uso.                                                                       |
| `InMemoryTaskRepository` | Implementación temporal del repositorio.                                                                                     |
| `repository_provider`    | Proporciona una instancia compartida del repositorio para los componentes que necesitan acceder al mismo conjunto de tareas. |

### Interfaz HTTP

Actualmente se exponen:

```text
POST  /academic/tasks
GET   /academic/tasks
PATCH /academic/tasks/{task_id}
PATCH /academic/tasks/{task_id}/complete
```

Todas las operaciones utilizan el usuario autenticado obtenido desde el módulo Usuario.

### Aislamiento de datos

El identificador del usuario se propaga hasta los casos de uso:

```text
JWT
 │
 ▼
Usuario.get_authenticated_user_id()
 │
 ▼
Academic API
 │
 ▼
Use Case
 │
 ▼
TaskRepository
```

De esta manera, la consulta y modificación de tareas se realizan dentro del contexto del estudiante autenticado.

---

### 5.2.3 Módulo AI

### Responsabilidad

El módulo **AI** proporciona la interfaz de asistente conversacional de TAIA.

Su responsabilidad es recibir mensajes del usuario, mantener el contexto mínimo necesario de la conversación, solicitar al LLM una interpretación y ejecutar las operaciones académicas correspondientes mediante un puerto.

El LLM no accede directamente al repositorio académico.

### Estructura

```text
AI
│
├── adapters/
│   ├── inbound/
│   │   └── api.py
│   │
│   └── outbound/
│       ├── academic_gateway.py
│       ├── gemini_llm.py
│       ├── fake_llm.py
│       └── in_memory_conversation_store.py
│
├── application/
│   ├── dto.py
│   ├── replies.py
│   │
│   ├── ports/
│   │   ├── academic_gateway.py
│   │   ├── conversation_store.py
│   │   └── llm.py
│   │
│   └── use_cases/
│       └── handle_message.py
│
└── domain/
    ├── conversation.py
    └── messages.py
```

### Bloques principales

| Bloque                      | Responsabilidad                                                                     |
| --------------------------- | ----------------------------------------------------------------------------------- |
| `AI API`                    | Recibe mensajes HTTP autenticados.                                                  |
| `HandleUserMessageUseCase`  | Coordina la interpretación y ejecución de una solicitud.                            |
| `LLM Port`                  | Abstrae el proveedor de inteligencia artificial.                                    |
| `GeminiLLM`                 | Adaptador del proveedor Gemini.                                                     |
| `FakeLLM`                   | Implementación utilizada en pruebas.                                                |
| `AcademicGateway`           | Puerto mediante el cual AI interactúa con Academic.                                 |
| `AcademicGatewayAdapter`    | Traduce las operaciones del contexto AI hacia los casos de uso del módulo Academic. |
| `ConversationStore`         | Puerto utilizado para mantener el estado de conversación.                           |
| `InMemoryConversationStore` | Implementación temporal del almacenamiento de conversaciones.                       |
| `Conversation`              | Representa el contexto de una conversación.                                         |
| `IncomingRequest`           | Representa el mensaje recibido por el asistente.                                    |

### Interfaz HTTP

```text
POST /ai/message
```

El endpoint exige autenticación.

La entrada contiene:

```text
text
channel
```

y la salida contiene:

```text
text
awaiting_confirmation
```

### Aislamiento arquitectónico

El recorrido de AI hacia Academic se realiza mediante:

```text
AI
 │
 ▼
AcademicGateway
 │
 ▼
AcademicGatewayAdapter
 │
 ▼
Academic Use Cases
 │
 ▼
TaskRepository
```

El LLM no conoce:

* `TaskRepository`
* `InMemoryTaskRepository`
* la entidad `Task`
* los detalles internos de persistencia.

Esto permite sustituir Gemini sin modificar las reglas del dominio académico.

---

### 5.2.4 Módulo Reminders

### Responsabilidad

El módulo **Reminders** administra recordatorios asociados a tareas académicas.

Sus responsabilidades actuales son:

* Crear recordatorios.
* Consultar recordatorios.
* Consultar un recordatorio específico.
* Editar recordatorios.
* Eliminar recordatorios.
* Marcar recordatorios como completados.
* Validar la existencia y pertenencia de la tarea académica asociada.
* Construir notificaciones.
* Enviar notificaciones mediante Telegram.

### Estructura

```text
Reminders
│
├── adapters/
│   ├── inbound/
│   │   └── http_controller.py
│   │
│   └── outbound/
│       ├── academic_task_lookup_adapter.py
│       ├── in_memory_reminder_repository.py
│       ├── repository_provider.py
│       ├── notification_provider.py
│       ├── telegram_bot_client.py
│       └── telegram_notification_sender.py
│
├── application/
│   ├── ports/
│   │   ├── inbound/
│   │   │   └── reminder_ports.py
│   │   │
│   │   └── outbound/
│   │       ├── academic_task_lookup.py
│   │       ├── notification_sender.py
│   │       └── reminder_repository.py
│   │
│   └── use_cases/
│       ├── create_reminder.py
│       ├── list_reminders.py
│       ├── get_reminder.py
│       ├── edit_reminder.py
│       ├── delete_reminder.py
│       ├── mark_reminder_completed.py
│       ├── schedule_notification.py
│       └── send_notification.py
│
└── domain/
    └── entities/
        ├── reminder.py
        ├── notification.py
        └── reminder_schedule.py
```

### Bloques principales

| Bloque                         | Responsabilidad                                                           |
| ------------------------------ | ------------------------------------------------------------------------- |
| `Reminders HTTP Controller`    | Expone las operaciones HTTP de recordatorios.                             |
| `CreateReminderUseCase`        | Valida y crea un recordatorio.                                            |
| `ListRemindersUseCase`         | Recupera los recordatorios del usuario.                                   |
| `GetReminderUseCase`           | Recupera un recordatorio verificando pertenencia.                         |
| `EditReminderUseCase`          | Actualiza un recordatorio no completado.                                  |
| `DeleteReminderUseCase`        | Elimina un recordatorio verificando pertenencia.                          |
| `MarkReminderCompletedUseCase` | Marca un recordatorio como completado.                                    |
| `ScheduleNotificationUseCase`  | Construye una notificación a partir del recordatorio.                     |
| `SendNotificationUseCase`      | Envía una notificación mediante el puerto correspondiente.                |
| `ReminderRepository`           | Puerto de persistencia de recordatorios.                                  |
| `InMemoryReminderRepository`   | Persistencia temporal del módulo.                                         |
| `AcademicTaskLookup`           | Puerto para verificar tareas académicas relacionadas.                     |
| `AcademicTaskLookupAdapter`    | Conecta Reminders con el repositorio/capa de consulta de Academic.        |
| `NotificationSender`           | Puerto de salida para el envío de notificaciones.                         |
| `TelegramNotificationSender`   | Implementación del envío mediante Telegram.                               |
| `TelegramBotApiClient`         | Cliente que encapsula la comunicación con Telegram Bot API.               |
| `Reminder`                     | Entidad de dominio del recordatorio.                                      |
| `Notification`                 | Entidad utilizada para representar una notificación preparada para envío. |
| `ReminderSchedule`             | Estructura relacionada con la organización de recordatorios.              |

### Interfaces HTTP

```text
POST   /reminders
GET    /reminders
GET    /reminders/{reminder_id}
PATCH  /reminders/{reminder_id}
DELETE /reminders/{reminder_id}
POST   /reminders/{reminder_id}/complete
POST   /reminders/{reminder_id}/notify
```

### Integración con Academic

Un recordatorio puede estar asociado a una tarea académica.

La creación no confía únicamente en el `task_id` recibido por HTTP. El caso de uso utiliza:

```text
Reminders
   │
   ▼
AcademicTaskLookup
   │
   ▼
AcademicTaskLookupAdapter
   │
   ▼
Academic
```

El adaptador comprueba que la tarea:

1. exista;
2. pertenezca al usuario autenticado.

Si la condición no se cumple, el recordatorio no se crea.

### Integración con Telegram

El envío se desacopla mediante:

```text
SendNotificationUseCase
        │
        ▼
NotificationSender
        │
        ▼
TelegramNotificationSender
        │
        ▼
TelegramBotApiClient
        │
        ▼
Telegram Bot API
```

El caso de uso no conoce los detalles HTTP de Telegram.

---

## 5.3. Integración entre los cuatro módulos

Los módulos forman un monolito modular y se comunican mediante interfaces y adaptadores.

```text
                         ┌───────────────┐
                         │    Usuario    │
                         │               │
                         │ JWT / Identity│
                         └───────┬───────┘
                                 │
                       authenticated user_id
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
         ┌────────────┐   ┌────────────┐   ┌────────────┐
         │ Academic   │   │     AI     │   │ Reminders  │
         │            │   │            │   │            │
         │ Tasks      │◄──│ Gateway    │──►│ Reminders  │
         │ Repository │   │ LLM        │   │ Notification│
         └─────┬──────┘   └────────────┘   └─────┬──────┘
               │                                  │
               │                                  │
               ▼                                  ▼
       InMemoryTaskRepository             Telegram adapter
                                              │
                                              ▼
                                      Telegram Bot API
```

Las relaciones principales son:

| Origen    | Destino  | Mecanismo                           |
| --------- | -------- | ----------------------------------- |
| Academic  | Usuario  | `get_authenticated_user_id`         |
| AI        | Usuario  | `get_authenticated_user_id`         |
| Reminders | Usuario  | `get_authenticated_user_id`         |
| AI        | Academic | `AcademicGateway`                   |
| Reminders | Academic | `AcademicTaskLookup`                |
| Reminders | Telegram | `NotificationSender`                |
| Usuario   | Telegram | vinculación mediante token temporal |
| AI        | Gemini   | `LLM` port / `GeminiLLM`            |

---

## 5.4. Composición de la aplicación

El punto de composición del backend se encuentra en `backend/app/main.py`.

Actualmente se registran los routers:

```text
FastAPI
 │
 ├── /users
 ├── /academic/tasks
 ├── /ai
 ├── /reminders
 └── /health
```

```python
app.include_router(academic_router)
app.include_router(usuario_router)
app.include_router(ai_router)
app.include_router(reminders_router)
```

La aplicación continúa siendo una única unidad desplegable.

---

## 5.5. Persistencia actual

El corte actual utiliza implementaciones en memoria.

```text
Usuario
   └── InMemoryUserRepository

Academic
   └── InMemoryTaskRepository

AI
   └── InMemoryConversationStore

Reminders
   └── InMemoryReminderRepository
```

Estas implementaciones permiten ejecutar pruebas y recorridos completos sin depender todavía de PostgreSQL.

Los puertos de persistencia permiten sustituir posteriormente estas implementaciones por adaptadores basados en PostgreSQL sin modificar las reglas principales de los casos de uso.

---

## 5.6. Límites actuales de los bloques

La arquitectura actual debe distinguir entre componentes implementados y componentes previstos.

### Implementado

* API FastAPI.
* Módulo Usuario.
* Autenticación JWT.
* Vinculación de Telegram.
* Módulo Academic.
* Registro, consulta, actualización y finalización de tareas.
* Módulo AI.
* Gateway entre AI y Academic.
* Adaptador para Gemini.
* Almacenamiento de conversación en memoria.
* Módulo Reminders.
* CRUD de recordatorios.
* Asociación de recordatorios con tareas académicas.
* Construcción y envío de notificaciones mediante Telegram.
* Repositorios en memoria.

### Pendiente o sujeto a evolución

* Persistencia definitiva en PostgreSQL.
* Scheduler persistente para disparar automáticamente los recordatorios al llegar `scheduled_at`.
* Implementación completa de la aplicación Flutter.
* Integración productiva de todos los flujos de Telegram como canal de entrada.
* Validación de rendimiento en infraestructura desplegada.
* Evolución de las capacidades avanzadas de IA como RAG, embeddings o búsqueda semántica.