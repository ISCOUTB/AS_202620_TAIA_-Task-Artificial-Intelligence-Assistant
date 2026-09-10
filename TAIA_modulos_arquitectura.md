# TAIA --- Definición de módulos y arquitectura interna

## 1. Propósito

Este documento define la propuesta de organización interna de los
módulos principales de TAIA como un **monolito modular**, aplicando una
organización interna inspirada en **Arquitectura Hexagonal (Ports &
Adapters)**.

Los módulos propuestos son:

1.  **Usuario**
2.  **Académico**
3.  **IA / Asistente**
4.  **Recordatorios / Notificaciones**

La separación busca establecer responsabilidades claras, propiedad de
datos y dependencias controladas antes de implementar el código
definitivo.

> **Estado:** propuesta arquitectónica. El proyecto actualmente cuenta
> con un corte vertical de prueba, por lo que los elementos indicados
> como posibles entidades, casos de uso o adaptadores deben validarse
> contra el alcance definitivo antes de implementarse.

------------------------------------------------------------------------

# 2. Principios generales

## 2.1 Monolito modular

Los cuatro módulos vivirán inicialmente dentro del mismo backend de
TAIA.

Esto **no significa que cada módulo sea un microservicio**.

La separación se realiza a nivel lógico y de código:

``` text
TAIA Backend
│
├── Usuario
├── Académico
├── IA / Asistente
└── Recordatorios / Notificaciones
```

Cada módulo debe tener:

-   un dominio propio;
-   casos de uso propios;
-   puertos de entrada y salida;
-   adaptadores propios cuando corresponda;
-   reglas de negocio propias;
-   propiedad clara sobre sus datos.

## 2.2 Organización interna

Cada módulo puede seguir una estructura como:

``` text
modulo/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── services/
│   └── rules/
│
├── application/
│   ├── use_cases/
│   ├── dto/
│   └── ports/
│       ├── inbound/
│       └── outbound/
│
└── adapters/
    ├── inbound/
    └── outbound/
```

### Domain

Contiene las reglas y conceptos propios del negocio.

No debería depender directamente de:

-   FastAPI;
-   PostgreSQL;
-   Telegram;
-   Gemini;
-   frameworks;
-   detalles HTTP.

### Application

Orquesta los casos de uso.

Coordina el dominio y utiliza los puertos necesarios para interactuar
con elementos externos.

### Ports

Definen las interfaces mediante las cuales el módulo recibe solicitudes
o solicita servicios externos.

#### Puertos de entrada

Representan las operaciones que el módulo ofrece.

Ejemplo:

``` text
RegistrarUsuario
IniciarSesion
GenerarVinculacionTelegram
```

#### Puertos de salida

Representan dependencias que el módulo necesita de elementos externos.

Ejemplo:

``` text
UserRepository
PasswordHasher
TokenService
```

### Adapters

Conectan los puertos con tecnologías concretas.

Ejemplo:

``` text
PostgresUserRepository
TelegramBotAdapter
GeminiAdapter
```

------------------------------------------------------------------------

# 3. Módulo Usuario

## 3.1 Responsabilidad

El módulo **Usuario** administra la identidad y la cuenta del usuario
dentro de TAIA.

También es responsable de permitir la **vinculación de una cuenta TAIA
existente con una cuenta de Telegram existente**.

El módulo no crea cuentas de Telegram.

Telegram es un sistema externo.

## 3.2 Responsabilidades principales

-   Registrar usuarios de TAIA.
-   Autenticar usuarios.
-   Gestionar información básica del perfil.
-   Gestionar credenciales.
-   Gestionar la sesión o mecanismo de autenticación.
-   Generar procesos de vinculación con Telegram.
-   Confirmar la vinculación con Telegram.
-   Desvincular una cuenta de Telegram.
-   Consultar el estado de vinculación.

## 3.3 Lo que NO pertenece al módulo

No debe ser responsable de:

-   crear tareas académicas;
-   interpretar solicitudes mediante IA;
-   enviar recordatorios;
-   almacenar conversaciones completas con Gemini;
-   administrar la infraestructura de Telegram;
-   administrar datos académicos.

------------------------------------------------------------------------

## 3.4 Dominio

### Entidad `Usuario`

Posibles atributos:

``` text
Usuario
├── id
├── nombre
├── email
├── password_hash
└── estado
```

Los atributos exactos deben ajustarse al modelo definitivo.

### Concepto `VinculacionTelegram`

Representa la relación entre una cuenta TAIA y una cuenta externa de
Telegram.

Posibles datos:

``` text
VinculacionTelegram
├── usuario_id
├── telegram_user_id
├── fecha_vinculacion
└── estado
```

### Reglas de negocio

1.  Un usuario TAIA puede tener como máximo una cuenta de Telegram
    vinculada.
2.  Una cuenta de Telegram puede estar vinculada como máximo a un
    usuario TAIA.
3.  La vinculación debe ser autorizada mediante un mecanismo temporal y
    seguro.
4.  Un token de vinculación no debe poder reutilizarse indefinidamente.
5.  Desvincular Telegram no elimina al usuario TAIA.
6.  Telegram no es dueño de la identidad del usuario dentro de TAIA.

------------------------------------------------------------------------

## 3.5 Casos de uso

### Gestión de cuenta

``` text
RegistrarUsuario
IniciarSesion
CerrarSesion
ObtenerPerfil
EditarPerfil
CambiarContraseña
```

### Vinculación con Telegram

``` text
GenerarVinculacionTelegram
ConfirmarVinculacionTelegram
ConsultarVinculacionTelegram
DesvincularTelegram
```

### Flujo conceptual

``` text
Usuario
   │
   ▼
TAIA
   │
   ├── Genera token temporal
   │
   ▼
Enlace de vinculación
   │
   ▼
Telegram
   │
   ├── /start <token>
   │
   ▼
TAIA valida token
   │
   ▼
Cuenta vinculada
```

------------------------------------------------------------------------

## 3.6 Puertos de entrada

``` text
UsuarioUseCases
├── registrar()
├── iniciarSesion()
├── cerrarSesion()
├── obtenerPerfil()
├── editarPerfil()
├── cambiarContraseña()
├── generarVinculacionTelegram()
├── confirmarVinculacionTelegram()
├── consultarVinculacionTelegram()
└── desvincularTelegram()
```

------------------------------------------------------------------------

## 3.7 Puertos de salida

Posibles interfaces:

``` text
UserRepository
TelegramLinkRepository
PasswordHasher
TokenService
TelegramBotGateway
```

### `UserRepository`

Responsable de persistir y consultar usuarios.

### `TelegramLinkRepository`

Responsable de almacenar y consultar la relación de vinculación.

### `PasswordHasher`

Abstrae el mecanismo utilizado para proteger contraseñas.

### `TokenService`

Puede utilizarse para tokens de sesión o tokens temporales de
vinculación.

### `TelegramBotGateway`

Abstrae la comunicación necesaria con Telegram.

------------------------------------------------------------------------

## 3.8 Posibles adaptadores

### Entrada

``` text
UserRouter
UserController
```

Podrían recibir solicitudes HTTP provenientes de Flutter.

### Salida

``` text
PostgresUserRepository
PostgresTelegramLinkRepository
BcryptPasswordHasher
JwtTokenService
TelegramBotAdapter
```

El uso concreto de JWT, bcrypt u otra tecnología queda sujeto a la
decisión técnica definitiva.

------------------------------------------------------------------------

# 4. Módulo Académico

## 4.1 Responsabilidad

El módulo **Académico** administra la información académica que TAIA
necesita para ayudar al estudiante a organizar sus actividades.

Su primera entidad validada en el corte vertical es `Task`, pero el
modelo puede crecer conforme se implementen los requisitos.

## 4.2 Posibles responsabilidades

-   Crear tareas.
-   Consultar tareas.
-   Actualizar tareas.
-   Eliminar tareas.
-   Gestionar materias.
-   Gestionar exámenes.
-   Gestionar clases u otros elementos académicos si forman parte del
    alcance final.

## 4.3 Lo que NO pertenece al módulo

No debe:

-   administrar usuarios;
-   autenticarse directamente;
-   comunicarse directamente con Gemini para interpretar lenguaje
    natural;
-   enviar mensajes de Telegram;
-   administrar tokens de autenticación.

------------------------------------------------------------------------

## 4.4 Dominio

### Entidad `Task`

Posibles atributos:

``` text
Task
├── id
├── user_id
├── title
├── description
├── due_date
├── priority
└── status
```

`user_id` permite asociar una tarea con un usuario, pero **Académico no
se convierte por ello en dueño de los datos de Usuario**.

### Posibles entidades futuras

``` text
Subject
Exam
Class
```

Estas solamente deben incorporarse si forman parte del alcance real del
sistema.

### Posibles objetos de valor

``` text
TaskId
DueDate
Priority
TaskStatus
```

------------------------------------------------------------------------

## 4.5 Reglas de negocio

Ejemplos:

1.  Una tarea debe pertenecer a un usuario.
2.  Una tarea debe tener información mínima válida.
3.  La fecha de entrega debe cumplir las reglas definidas por el
    dominio.
4.  Solo el propietario de una tarea puede modificarla o eliminarla.
5.  El estado de una tarea debe pertenecer a los estados permitidos.
6.  La prioridad debe pertenecer al conjunto definido por el dominio.

Las reglas definitivas deberán derivarse de los requisitos funcionales.

------------------------------------------------------------------------

## 4.6 Casos de uso

### Tareas

``` text
CrearTask
ObtenerTask
ListarTasks
ActualizarTask
EliminarTask
CompletarTask
```

### Posibles casos futuros

``` text
CrearSubject
ListarSubjects
CrearExam
ListarExams
CrearClass
ListarClasses
```

No se deben implementar casos de uso que no estén respaldados por el
alcance del proyecto.

------------------------------------------------------------------------

## 4.7 Puertos de entrada

``` text
AcademicUseCases
├── crearTask()
├── obtenerTask()
├── listarTasks()
├── actualizarTask()
├── eliminarTask()
└── completarTask()
```

------------------------------------------------------------------------

## 4.8 Puertos de salida

``` text
TaskRepository
SubjectRepository
ExamRepository
```

Inicialmente puede existir solamente:

``` text
TaskRepository
```

Los demás se agregan cuando existan esas entidades en el dominio.

------------------------------------------------------------------------

## 4.9 Posibles adaptadores

### Entrada

``` text
AcademicRouter
TaskController
```

### Salida

``` text
PostgresTaskRepository
PostgresSubjectRepository
PostgresExamRepository
```

El repositorio concreto implementa el puerto definido por el módulo.

------------------------------------------------------------------------

# 5. Módulo IA / Asistente

## 5.1 Responsabilidad

El módulo **IA / Asistente** se encarga de interpretar solicitudes del
usuario mediante lenguaje natural y convertirlas en una intención que
TAIA pueda procesar.

La IA no debe convertirse en dueña de los datos académicos.

## 5.2 Ejemplo

El usuario podría expresar:

``` text
"Recuérdame entregar el trabajo de arquitectura mañana a las 8."
```

El módulo IA podría interpretar:

``` text
Intent
├── action: CREATE_REMINDER
├── description: "Entregar el trabajo de arquitectura"
└── scheduled_at: ...
```

La IA interpreta la solicitud.

El módulo correspondiente ejecuta la operación.

------------------------------------------------------------------------

## 5.3 Lo que NO pertenece al módulo

IA no debe ser propietaria de:

-   `Task`;
-   `Usuario`;
-   `Reminder`;
-   `Subject`;
-   credenciales;
-   datos de PostgreSQL de otros módulos.

Por ejemplo, IA no debería ejecutar directamente:

``` text
INSERT INTO tasks ...
```

En su lugar, debería utilizar un puerto/caso de uso del módulo
correspondiente.

------------------------------------------------------------------------

## 5.4 Dominio

### Posible concepto `UserIntent`

Representa una intención interpretada.

``` text
UserIntent
├── action
├── parameters
└── confidence
```

Ejemplos:

``` text
CREATE_TASK
CREATE_REMINDER
LIST_TASKS
UPDATE_TASK
DELETE_TASK
```

El conjunto definitivo dependerá de las funcionalidades de TAIA.

### `AIRequest`

Representa la información enviada al proveedor de IA.

### `AIResponse`

Representa el resultado recibido.

Estos conceptos pueden ser objetos de valor o DTOs y **no necesariamente
entidades persistentes**.

------------------------------------------------------------------------

## 5.5 Casos de uso

``` text
InterpretarSolicitud
ProcesarSolicitudIA
GenerarRespuesta
```

También puede existir un caso de uso de mayor nivel:

``` text
ProcesarSolicitudDelUsuario
```

que coordine:

``` text
Solicitud
   ↓
IA interpreta
   ↓
UserIntent
   ↓
Módulo correspondiente
   ↓
Resultado
   ↓
Respuesta al usuario
```

------------------------------------------------------------------------

## 5.6 Puertos de entrada

``` text
AssistantUseCases
├── interpretarSolicitud()
├── procesarSolicitud()
└── generarRespuesta()
```

------------------------------------------------------------------------

## 5.7 Puertos de salida

Principalmente:

``` text
AIProvider
```

Posibles interfaces adicionales, según el diseño final:

``` text
AcademicGateway
ReminderGateway
UserContextGateway
```

Estos gateways son importantes porque evitan que IA dependa directamente
de las implementaciones internas de otros módulos.

------------------------------------------------------------------------

## 5.8 Posibles adaptadores

### Entrada

``` text
AssistantRouter
TelegramCommandAdapter
```

El segundo solamente sería necesario si el flujo de entrada desde
Telegram necesita interactuar directamente con el asistente.

### Salida

``` text
GeminiAdapter
```

En el futuro podría existir:

``` text
OpenAIAdapter
OtherAIProviderAdapter
```

La intención es que el dominio y la aplicación no dependan directamente
de Gemini.

------------------------------------------------------------------------

# 6. Módulo Recordatorios / Notificaciones

## 6.1 Responsabilidad

Este módulo administra la planificación y entrega de recordatorios al
usuario.

Su responsabilidad principal es:

``` text
qué recordar
cuándo recordarlo
a quién
por qué canal enviarlo
```

No es dueño de la identidad completa del usuario ni de las tareas
académicas.

------------------------------------------------------------------------

## 6.2 Dominio

### Entidad `Reminder`

Posibles atributos:

``` text
Reminder
├── id
├── user_id
├── message
├── scheduled_at
├── status
└── reference
```

`reference` podría permitir relacionar el recordatorio con una entidad
externa, por ejemplo una tarea académica.

La forma exacta debe definirse antes de implementar persistencia.

### Posibles conceptos

``` text
ReminderSchedule
Notification
NotificationStatus
```

Solo deben convertirse en entidades si el comportamiento del sistema lo
justifica.

------------------------------------------------------------------------

## 6.3 Reglas de negocio

Ejemplos:

1.  Un recordatorio pertenece a un usuario.
2.  Un recordatorio debe tener una fecha/hora válida.
3.  Un recordatorio pendiente puede ser enviado una sola vez.
4.  Un recordatorio cancelado no debe enviarse.
5.  El envío debe utilizar un canal disponible para el usuario.
6.  El módulo no modifica directamente las tareas académicas.

------------------------------------------------------------------------

## 6.4 Casos de uso

``` text
CrearReminder
ObtenerReminder
ListarReminders
ActualizarReminder
EliminarReminder
CompletarReminder
ProgramarReminder
CancelarReminder
```

Algunos pueden combinarse si el diseño final demuestra que no necesitan
casos separados.

------------------------------------------------------------------------

## 6.5 Puertos de entrada

``` text
ReminderUseCases
├── crearReminder()
├── obtenerReminder()
├── listarReminders()
├── actualizarReminder()
├── eliminarReminder()
├── programarReminder()
└── cancelarReminder()
```

------------------------------------------------------------------------

## 6.6 Puertos de salida

``` text
ReminderRepository
NotificationSender
Scheduler
```

### `ReminderRepository`

Persistencia de recordatorios.

### `NotificationSender`

Abstrae el canal mediante el cual se envía la notificación.

### `Scheduler`

Abstrae el mecanismo de programación de tareas futuras.

------------------------------------------------------------------------

## 6.7 Posibles adaptadores

### Entrada

``` text
ReminderRouter
ReminderController
```

### Salida

``` text
PostgresReminderRepository
TelegramNotificationAdapter
SchedulerAdapter
```

El `TelegramNotificationAdapter` utiliza Telegram como canal de entrega,
pero **Telegram no se convierte en dueño del dominio de Recordatorios**.

------------------------------------------------------------------------

# 7. Relaciones entre módulos

La regla general debe ser:

``` text
Usuario
   │
   ├──────────────► identidad
   │
Académico
   │
   ├──────────────► información académica
   │
IA / Asistente
   │
   ├──────────────► interpretación y orquestación
   │
Recordatorios
   │
   └──────────────► programación y notificaciones
```

Una interacción posible sería:

``` text
Usuario
   │
   ▼
IA / Asistente
   │
   ├──► Académico
   │
   └──► Recordatorios
```

Mientras que:

``` text
Recordatorios ──► Usuario
```

debería consumir solamente la información mínima necesaria para enviar
una notificación, no acceder directamente a toda la estructura interna
del módulo Usuario.

------------------------------------------------------------------------

# 8. Propiedad de datos

La propiedad debe quedar explícita desde el diseño.

  Dato / entidad           Módulo dueño
  ------------------------ ---------------------------------
  Usuario                  Usuario
  Credenciales             Usuario
  Vinculación Telegram     Usuario
  Task                     Académico
  Subject                  Académico
  Exam                     Académico
  Reminder                 Recordatorios
  Notification             Recordatorios
  UserIntent               IA / Asistente
  AIRequest / AIResponse   IA / Asistente, si se persisten

> Las entidades `Subject`, `Exam`, `Notification`, etc. son propuestas
> de diseño y deben confirmarse contra el alcance real antes de
> declararlas como entidades existentes del código.

------------------------------------------------------------------------

# 9. Reglas de dependencia

Se busca evitar dependencias como:

``` text
IA → PostgreSQL
IA → TaskModel
IA → Telegram API
```

En cambio:

``` text
IA
 │
 ▼
Puerto
 │
 ▼
Adaptador
```

Por ejemplo:

``` text
IA
 │
 ▼
AIProvider
 │
 ▼
GeminiAdapter
 │
 ▼
Gemini
```

Y:

``` text
Académico
 │
 ▼
TaskRepository
 │
 ▼
PostgresTaskRepository
 │
 ▼
PostgreSQL
```

------------------------------------------------------------------------

# 10. Integración con Telegram

Telegram es un sistema externo.

Debe existir una separación entre:

``` text
Dominio TAIA
```

y:

``` text
Telegram API
```

Por ello se propone:

``` text
TAIA
 │
 ├── Usuario
 │     └── TelegramLinkRepository
 │
 └── Recordatorios
       └── NotificationSender
                │
                ▼
          TelegramAdapter
                │
                ▼
             Telegram
```

Esto permite que el módulo Usuario sea responsable de **vincular la
identidad**, mientras que Recordatorios puede ser responsable de
**enviar notificaciones**.

Son responsabilidades diferentes.

------------------------------------------------------------------------

# 11. Integración con Gemini

Gemini también es un sistema externo.

La dependencia debería quedar aislada:

``` text
IA / Asistente
      │
      ▼
  AIProvider
      │
      ▼
 GeminiAdapter
      │
      ▼
    Gemini
```

De esta manera, cambiar Gemini por otro proveedor no debería requerir
modificar las reglas centrales del módulo IA.

------------------------------------------------------------------------

# 12. Estructura propuesta del backend

Una posible estructura física es:

``` text
backend/
└── app/
    ├── modules/
    │   ├── usuario/
    │   │   ├── domain/
    │   │   ├── application/
    │   │   └── adapters/
    │   │
    │   ├── academico/
    │   │   ├── domain/
    │   │   ├── application/
    │   │   └── adapters/
    │   │
    │   ├── ia/
    │   │   ├── domain/
    │   │   ├── application/
    │   │   └── adapters/
    │   │
    │   └── recordatorios/
    │       ├── domain/
    │       ├── application/
    │       └── adapters/
    │
    └── shared/
        └── ...
```

`shared` debe mantenerse pequeño. No debe convertirse en un lugar donde
se coloque cualquier código utilizado por varios módulos, porque eso
podría terminar creando dependencias ocultas entre contextos.

------------------------------------------------------------------------

# 13. Diferencia entre módulo, dominio y adaptador

Es importante no confundir estos conceptos.

``` text
MÓDULO
│
├── DOMAIN
│   └── ¿Qué significa este negocio?
│
├── APPLICATION
│   └── ¿Qué operaciones puede realizar?
│
├── PORTS
│   └── ¿Cómo se comunica con el exterior?
│
└── ADAPTERS
    └── ¿Cómo conectamos esas interfaces con tecnología real?
```

Por ejemplo:

``` text
Académico
│
├── Domain
│   └── Task
│
├── Application
│   └── CrearTask
│
├── Port
│   └── TaskRepository
│
└── Adapter
    └── PostgresTaskRepository
```

------------------------------------------------------------------------

# 14. Relación con arc42

Esta propuesta puede utilizarse como base para varias partes de la
documentación arquitectónica.

En **arc42 sección 5**, los módulos pueden aparecer como building blocks
principales y posteriormente refinarse. La sección 8 puede documentar
conceptos que atraviesan varios módulos, como el lenguaje ubicuo, el
modelo de dominio, ports & adapters y reglas de integración. arc42
recomienda utilizar la sección 8 para conceptos transversales y para
documentar modelos de dominio que afectan múltiples building blocks.
citeturn0search0turn0search2

La separación entre contexto del sistema y sistemas externos también es
coherente con la recomendación de arc42 de delimitar claramente qué está
dentro del sistema y qué pertenece a su entorno. citeturn0search6

------------------------------------------------------------------------

# 15. Estado actual y siguiente paso

Esta definición debe considerarse **arquitectura objetivo**, no una
afirmación de que todas estas entidades ya existen en el código.

Actualmente el proyecto cuenta con un corte vertical de prueba. Por
ello, el siguiente proceso recomendado es:

1.  Revisar qué código real existe actualmente.
2.  Identificar qué elementos del corte vertical pertenecen a cada
    módulo.
3.  Confirmar las entidades reales.
4.  Confirmar los casos de uso respaldados por requisitos.
5.  Definir la propiedad de datos.
6.  Definir las relaciones entre contextos.
7.  Actualizar C4 nivel 3 si corresponde.
8.  Actualizar arc42 sección 8.
9.  Crear o actualizar ADR cuando una decisión arquitectónica cambie.
10. Implementar los módulos progresivamente.

La arquitectura no debe inventar entidades simplemente para llenar el
documento: cada entidad que se declare como existente debe poder
localizarse en el código cuando se haga la validación de S6.
