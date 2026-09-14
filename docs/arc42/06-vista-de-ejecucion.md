# 6. Vista de ejecución

La vista de ejecución describe cómo los bloques de TAIA colaboran durante la ejecución de escenarios relevantes.

La selección de escenarios se realiza por relevancia arquitectónica: se documentan los recorridos que muestran las interacciones importantes entre módulos, dependencias externas, validaciones, aislamiento de usuarios y manejo de errores.

Los recorridos principales se agrupan por los cuatro módulos del sistema y por sus integraciones.

---

## 6.1. Recorrido del módulo Usuario — Registro

### Flujo

```text
Estudiante
    │
    │ POST /users
    ▼
Usuario API
    │
    ▼
RegisterUserUseCase
    │
    ├── valida Email
    │
    ├── verifica usuario existente
    │
    ├── genera password hash
    │
    ▼
Usuario
    │
    ▼
UserRepository
    │
    ▼
InMemoryUserRepository
    │
    ▼
HTTP 201
```

### Secuencia

1. El estudiante envía nombre, correo y contraseña.
2. El adaptador HTTP recibe la solicitud.
3. `RegisterUserUseCase` valida el correo.
4. Se verifica que no exista otro usuario con el mismo correo.
5. La contraseña se transforma mediante `Pbkdf2PasswordHasher`.
6. Se crea la entidad `Usuario`.
7. El repositorio almacena el usuario.
8. La API devuelve la información pública del usuario.

### Errores relevantes

```text
Correo existente
      │
      ▼
HTTP 409 Conflict
```

```text
Datos inválidos
      │
      ▼
HTTP 422 Unprocessable Entity
```

---

## 6.2. Recorrido del módulo Usuario — Login

```text
Estudiante
    │
    │ POST /users/login
    ▼
Usuario API
    │
    ▼
LoginUserUseCase
    │
    ├── busca usuario
    │
    ├── verifica password
    │
    ▼
JwtTokenService
    │
    ▼
Access Token
    │
    ▼
HTTP 200
```

### Secuencia

1. El estudiante envía correo y contraseña.
2. `LoginUserUseCase` consulta el repositorio.
3. Se verifica la contraseña mediante el hasher.
4. Se valida que el usuario esté activo.
5. `JwtTokenService` genera el token.
6. El token se devuelve al cliente.

### Errores

```text
Credenciales inválidas
        │
        ▼
HTTP 401
```

```text
Usuario inactivo
        │
        ▼
HTTP 403
```

---

## 6.3. Recorrido del módulo Usuario — Autenticación de una solicitud

Este recorrido es transversal a los otros tres módulos.

```text
Cliente
   │
   │ Authorization: Bearer JWT
   ▼
HTTP Endpoint
   │
   ▼
IdentityService.authenticate()
   │
   ▼
JwtTokenService
   │
   ▼
GetCurrentUserUseCase
   │
   ▼
UserRepository
   │
   ├── usuario válido ─────► user_id
   │
   └── usuario inválido ───► HTTP 401
```

Una vez obtenido el `user_id`, el endpoint delega la operación al módulo correspondiente.

Esto permite que la identidad sea resuelta una sola vez en la frontera HTTP y que cada módulo aplique sus propias reglas de pertenencia.

---

## 6.4. Recorrido del módulo Usuario — Vinculación con Telegram

### Generación del enlace

```text
Estudiante autenticado
        │
        │ POST /users/me/telegram/link
        ▼
Usuario API
        │
        ▼
CreateTelegramLinkUseCase
        │
        ├── valida usuario
        ├── genera token
        ├── define expiración
        ▼
TelegramLinkRepository
        │
        ▼
Deep Link de Telegram
```

El token generado es temporal y está asociado al usuario autenticado.

### Confirmación

```text
Telegram
    │
    │ token + telegram_user_id
    ▼
POST /users/telegram/link/confirm
    │
    ▼
ConfirmTelegramLinkUseCase
    │
    ├── valida token
    ├── verifica expiración
    ├── verifica unicidad
    ▼
Usuario.link_telegram()
    │
    ▼
UserRepository
```

La vinculación se rechaza si:

* el token no existe;
* el token expiró;
* el token ya fue utilizado;
* el Telegram ya pertenece a otro usuario;
* el usuario ya tiene otra cuenta Telegram vinculada.

---

## 6.5. Recorrido del módulo Academic — Registro de tarea

```text
Estudiante autenticado
        │
        │ POST /academic/tasks
        ▼
Academic API
        │
        ▼
RegisterTaskUseCase
        │
        ▼
Task
        │
        ▼
TaskRepository
        │
        ▼
InMemoryTaskRepository
        │
        ▼
TaskResponse
        │
        ▼
HTTP 201
```

### Secuencia

1. El usuario envía los datos de la tarea.
2. FastAPI obtiene el `user_id` desde el JWT.
3. `RegisterTaskUseCase` recibe los datos.
4. Se crea la entidad `Task`.
5. El caso de uso utiliza `TaskRepository`.
6. `InMemoryTaskRepository` almacena la tarea.
7. Se devuelve `TaskResponse`.

### Validación

```text
Datos inválidos
      │
      ▼
InvalidTaskError
      │
      ▼
HTTP 422
```

---

## 6.6. Recorrido del módulo Academic — Consulta de tareas

```text
Cliente
   │
   │ GET /academic/tasks
   ▼
Academic API
   │
   ▼
ListTasksUseCase
   │
   ▼
TaskRepository
   │
   ▼
InMemoryTaskRepository
   │
   ▼
Filtrado por user_id
   │
   ▼
Lista de TaskResponse
```

El repositorio devuelve únicamente las tareas correspondientes al usuario autenticado.

Este escenario es especialmente relevante para **S4 — Acceso únicamente a datos del propio estudiante**.

---

## 6.7. Recorrido del módulo Academic — Actualización de tarea

```text
Cliente
   │
   │ PATCH /academic/tasks/{task_id}
   ▼
Academic API
   │
   ▼
UpdateTaskUseCase
   │
   ├── busca tarea
   ├── verifica user_id
   ├── actualiza campos
   ▼
TaskRepository
   │
   ▼
InMemoryTaskRepository
   │
   ▼
TaskResponse
```

Si la tarea no existe o no pertenece al usuario:

```text
TaskNotFoundError
      │
      ▼
HTTP 404
```

---

## 6.8. Recorrido del módulo Academic — Completar tarea

```text
Cliente
   │
   │ PATCH /academic/tasks/{task_id}/complete
   ▼
Academic API
   │
   ▼
CompleteTaskUseCase
   │
   ▼
TaskRepository
   │
   ▼
Task.update / estado completado
   │
   ▼
InMemoryTaskRepository
   │
   ▼
TaskResponse
```

El caso de uso verifica que la tarea corresponda al usuario autenticado antes de modificar su estado.

---

## 6.9. Recorrido del módulo AI — Mensaje simple

```text
Cliente autenticado
        │
        │ POST /ai/message
        ▼
AI API
        │
        ▼
HandleUserMessageUseCase
        │
        ├──────────────► ConversationStore
        │
        ▼
      LLM Port
        │
        ▼
   GeminiLLM
        │
        ▼
 Gemini API
        │
        ▼
Respuesta interpretada
        │
        ▼
HandleUserMessageUseCase
        │
        ▼
AIMessageResponse
```

### Secuencia

1. El usuario envía un mensaje.
2. El endpoint valida el JWT.
3. Se obtiene el `user_id`.
4. `HandleUserMessageUseCase` recibe un `IncomingRequest`.
5. El caso de uso utiliza el almacenamiento de conversación.
6. El puerto `LLM` abstrae al proveedor.
7. `GeminiLLM` traduce la solicitud hacia Gemini.
8. El resultado vuelve al caso de uso.
9. Se construye la respuesta del asistente.

Si Gemini no está configurado:

```text
GeminiLLM.from_env()
        │
        ▼
configuración ausente
        │
        ▼
HTTP 503
```

---

## 6.10. Recorrido del módulo AI — Registro de una tarea mediante lenguaje natural

Este es uno de los recorridos de mayor relevancia arquitectónica porque conecta AI con Academic.

```text
Estudiante
    │
    │ "Tengo que entregar ... el viernes"
    ▼
POST /ai/message
    │
    ▼
AI API
    │
    ▼
HandleUserMessageUseCase
    │
    ▼
LLM
    │
    ▼
Información estructurada
    │
    ▼
Validación / confirmación
    │
    ├── requiere confirmación
    │
    │      ▼
    │   respuesta al usuario
    │
    │      ▼
    │   "sí"
    │
    ▼
AcademicGateway
    │
    ▼
AcademicGatewayAdapter
    │
    ▼
RegisterTaskUseCase
    │
    ▼
TaskRepository
    │
    ▼
InMemoryTaskRepository
    │
    ▼
Task creada
    │
    ▼
AI Response
```

### Principio arquitectónico

El LLM **no crea directamente la tarea**.

La secuencia correcta es:

```text
Lenguaje natural
       │
       ▼
      LLM
       │
       ▼
Información estructurada
       │
       ▼
Validación
       │
       ▼
AcademicGateway
       │
       ▼
Academic Use Case
       │
       ▼
Domain
       │
       ▼
Repository
```

Esto mantiene las reglas de negocio fuera del modelo de lenguaje.

---

## 6.11. Recorrido del módulo AI — Consulta académica

```text
Estudiante
   │
   │ "¿Qué tareas tengo?"
   ▼
AI API
   │
   ▼
HandleUserMessageUseCase
   │
   ▼
LLM
   │
   ▼
Intención de consulta
   │
   ▼
AcademicGateway
   │
   ▼
AcademicGatewayAdapter
   │
   ▼
ListTasksUseCase
   │
   ▼
TaskRepository
   │
   ▼
Tareas del user_id
   │
   ▼
AcademicGateway
   │
   ▼
AI
   │
   ▼
Respuesta al estudiante
```

El `user_id` autenticado se conserva durante el recorrido para evitar que la consulta acceda a tareas de otro usuario.

---

## 6.12. Recorrido del módulo Reminders — Creación

```text
Estudiante autenticado
        │
        │ POST /reminders
        ▼
Reminders Controller
        │
        ▼
CreateReminderUseCase
        │
        ├── valida mensaje
        ├── valida fecha futura
        │
        ▼
AcademicTaskLookup
        │
        ▼
AcademicTaskLookupAdapter
        │
        ▼
Academic Repository
        │
        ├── tarea inexistente ─────► error
        │
        └── tarea pertenece al usuario
                    │
                    ▼
              Reminder
                    │
                    ▼
        InMemoryReminderRepository
                    │
                    ▼
                HTTP 201
```

El recordatorio no puede asociarse arbitrariamente a una tarea perteneciente a otro estudiante.

---

## 6.13. Recorrido del módulo Reminders — Consulta

```text
Cliente
   │
   │ GET /reminders
   ▼
Reminders Controller
   │
   ▼
ListRemindersUseCase
   │
   ▼
ReminderRepository
   │
   ▼
InMemoryReminderRepository
   │
   ▼
Filtrado por user_id
   │
   ▼
Lista de ReminderResponse
```

La consulta solamente devuelve los recordatorios del usuario autenticado.

---

## 6.14. Recorrido del módulo Reminders — Consulta individual

```text
GET /reminders/{id}
        │
        ▼
Reminders Controller
        │
        ▼
GetReminderUseCase
        │
        ▼
ReminderRepository
        │
        ├── no existe ───────► HTTP 404
        │
        ├── pertenece a otro usuario
        │                     │
        │                     └──► HTTP 404
        │
        ▼
ReminderResponse
```

El sistema no revela información sobre recordatorios de otros usuarios.

---

## 6.15. Recorrido del módulo Reminders — Edición

```text
PATCH /reminders/{id}
        │
        ▼
EditReminderUseCase
        │
        ├── verifica existencia
        ├── verifica ownership
        ├── verifica que no esté completado
        ├── valida nueva fecha
        │
        ▼
ReminderRepository
        │
        ▼
InMemoryReminderRepository
        │
        ▼
ReminderResponse
```

Un recordatorio completado no puede editarse.

---

## 6.16. Recorrido del módulo Reminders — Completar

```text
POST /reminders/{id}/complete
        │
        ▼
MarkReminderCompletedUseCase
        │
        ├── verifica existencia
        ├── verifica ownership
        │
        ▼
Reminder
        │
        ▼
is_completed = true
        │
        ▼
ReminderRepository
        │
        ▼
ReminderResponse
```

La operación es idempotente: si el recordatorio ya está completado, se mantiene en ese estado.

---

## 6.17. Recorrido del módulo Reminders — Envío de notificación

```text
Estudiante autenticado
        │
        │ POST /reminders/{id}/notify
        ▼
Reminders Controller
        │
        ▼
GetReminderUseCase
        │
        ▼
ReminderRepository
        │
        ▼
Reminder válido
        │
        ▼
ScheduleNotificationUseCase
        │
        ▼
Notification
        │
        ▼
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
        │
        ▼
NotificationResponse
```

### Fallo de envío

Si Telegram no puede recibir la notificación:

```text
Telegram Bot API
       │
       ▼
envío fallido
       │
       ▼
NotificationSender = False
       │
       ▼
HTTP 503
```

El sistema no presenta el envío como exitoso cuando el proveedor externo no confirma la operación.

---

## 6.18. Recorrido integrado — Usuario + Academic

Este escenario representa el flujo normal de autenticación y gestión académica.

```text
                    ┌───────────────┐
                    │   Estudiante  │
                    └───────┬───────┘
                            │
                            │ login
                            ▼
                    ┌───────────────┐
                    │    Usuario    │
                    └───────┬───────┘
                            │
                         JWT │
                            ▼
                    ┌───────────────┐
                    │    Academic   │
                    └───────┬───────┘
                            │
                            ▼
                         Task
                            │
                            ▼
                    TaskRepository
```

Este flujo establece el contexto de identidad que utilizarán AI y Reminders.

---

## 6.19. Recorrido integrado — Usuario + AI + Academic

Este escenario representa la captura inteligente.

```text
Estudiante
    │
    │ JWT + mensaje
    ▼
 Usuario
    │
    │ user_id
    ▼
   AI
    │
    ▼
  Gemini
    │
    ▼
interpretación
    │
    ▼
AcademicGateway
    │
    ▼
 Academic
    │
    ▼
 TaskRepository
    │
    ▼
 tarea
    │
    ▼
   AI
    │
    ▼
Estudiante
```

La característica importante es que AI funciona como **orquestador**, mientras Academic conserva la responsabilidad sobre la información académica.

---

## 6.20. Recorrido integrado — Usuario + Academic + Reminders

Este escenario representa la creación de un recordatorio asociado a una tarea.

```text
Estudiante
    │
    │ JWT
    ▼
 Usuario
    │
    │ user_id
    ▼
Reminders
    │
    │ task_id + user_id
    ▼
AcademicTaskLookup
    │
    ▼
Academic
    │
    ▼
TaskRepository
    │
    ├── tarea válida
    │
    ▼
CreateReminderUseCase
    │
    ▼
ReminderRepository
    │
    ▼
Reminder
```

Este recorrido garantiza que el recordatorio no pueda apuntar a información académica de otro usuario.

---

## 6.21. Recorrido integrado — Usuario + Reminders + Telegram

```text
Estudiante
    │
    │ JWT
    ▼
Usuario
    │
    │ user_id
    ▼
Reminders
    │
    ▼
ReminderRepository
    │
    ▼
Notification
    │
    ▼
NotificationSender
    │
    ▼
TelegramNotificationSender
    │
    ▼
Telegram Bot API
    │
    ▼
Estudiante en Telegram
```

La vinculación entre Usuario y Telegram permite que la notificación se entregue a la cuenta correspondiente.

---

## 6.22. Recorrido integrado completo — AI + Academic + Reminders

El flujo representa la evolución esperada de una interacción completa dentro de TAIA.

```text
                    Estudiante
                        │
                        │ mensaje
                        ▼
                   ┌─────────┐
                   │   AI    │
                   └────┬────┘
                        │
                        ▼
                     Gemini
                        │
                        ▼
                intención estructurada
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
        Registrar tarea       Consultar tarea
             │                     │
             ▼                     ▼
          Academic              Academic
             │                     │
             └──────────┬──────────┘
                        │
                        ▼
                     Task
                        │
                        ▼
                   Reminders
                        │
                        ▼
                    Reminder
                        │
                        ▼
                  Notification
                        │
                        ▼
                  Telegram
                        │
                        ▼
                    Usuario
```

Este escenario evidencia la separación de responsabilidades:

* **AI** interpreta.
* **Academic** gobierna la información académica.
* **Reminders** administra recordatorios.
* **Usuario** controla identidad.
* **Telegram** funciona como canal externo.

---

## 6.23. Manejo transversal de errores

Los módulos mantienen una frontera clara entre errores de aplicación y respuestas HTTP.

```text
Domain / Use Case
       │
       ▼
Error de negocio
       │
       ▼
HTTP Adapter
       │
       ▼
HTTP status code
```

Ejemplos:

| Situación                       | Módulo    | Resultado |
| ------------------------------- | --------- | --------- |
| Credenciales inválidas          | Usuario   | `401`     |
| Usuario inactivo                | Usuario   | `403`     |
| Correo ya registrado            | Usuario   | `409`     |
| JWT inválido                    | Usuario   | `401`     |
| Tarea no encontrada             | Academic  | `404`     |
| Datos de tarea inválidos        | Academic  | `422`     |
| Recordatorio inexistente        | Reminders | `404`     |
| Recordatorio de otro usuario    | Reminders | `404`     |
| Fecha de recordatorio no válida | Reminders | `422`     |
| Recordatorio completado editado | Reminders | `422`     |
| Gemini no configurado           | AI        | `503`     |
| Telegram no disponible          | Reminders | `503`     |

---

## 6.24. Resumen de recorridos arquitectónicos

Los escenarios principales documentados son:

| #  | Módulo / integración           | Escenario                                 |
| -- | ------------------------------ | ----------------------------------------- |
| 1  | Usuario                        | Registro                                  |
| 2  | Usuario                        | Login                                     |
| 3  | Usuario                        | Autenticación transversal                 |
| 4  | Usuario                        | Vinculación Telegram                      |
| 5  | Academic                       | Registro de tarea                         |
| 6  | Academic                       | Consulta de tareas                        |
| 7  | Academic                       | Actualización de tarea                    |
| 8  | Academic                       | Completar tarea                           |
| 9  | AI                             | Procesar mensaje                          |
| 10 | AI                             | Registrar tarea mediante lenguaje natural |
| 11 | AI                             | Consultar información académica           |
| 12 | Reminders                      | Crear recordatorio                        |
| 13 | Reminders                      | Listar recordatorios                      |
| 14 | Reminders                      | Consultar recordatorio                    |
| 15 | Reminders                      | Editar recordatorio                       |
| 16 | Reminders                      | Completar recordatorio                    |
| 17 | Reminders                      | Enviar notificación                       |
| 18 | Usuario + Academic             | Gestión autenticada de tareas             |
| 19 | Usuario + AI + Academic        | Captura inteligente                       |
| 20 | Usuario + Academic + Reminders | Recordatorio asociado a tarea             |
| 21 | Usuario + Reminders + Telegram | Entrega de notificación                   |
| 22 | AI + Academic + Reminders      | Flujo integrado                           |
| 23 | Transversal                    | Manejo de errores                         |


Estos escenarios representan los recorridos arquitectónicamente relevantes del estado actual de TAIA y muestran cómo los cuatro módulos colaboran dentro del monolito modular.