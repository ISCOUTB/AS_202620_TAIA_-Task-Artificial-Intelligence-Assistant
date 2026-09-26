# 7. Vista de despliegue

La arquitectura de despliegue distingue entre la **arquitectura objetivo** y el **corte vertical actualmente ejecutable**.

## 7.1. Arquitectura de despliegue objetivo

TAIA está previsto como un sistema con un backend central desplegado como una única aplicación y con servicios externos separados.

```text
                         ┌──────────────────┐
                         │    Estudiante    │
                         └────────┬─────────┘
                                  │
                         ┌────────┴─────────┐
                         │                  │
                         ▼                  ▼
                  ┌─────────────┐    ┌─────────────┐
                  │ Flutter App │    │   Telegram  │
                  │   Android   │    │  Bot API    │
                  └──────┬──────┘    └──────┬──────┘
                         │                  │
                         └─────────┬────────┘
                                   │
                              HTTP / Webhook
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Backend TAIA    │
                         │     FastAPI       │
                         │                   │
                         │  Monolito modular │
                         └───────┬───────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌────────────┐
              │PostgreSQL│ │  Gemini  │ │ Telegram   │
              │   DB     │ │   API    │ │ Bot API    │
              └──────────┘ └──────────┘ └────────────┘
```

El backend concentra la lógica de aplicación y actúa como frontera entre los clientes, los servicios externos y la persistencia. Gemini se utiliza como proveedor externo de interpretación de lenguaje natural y PostgreSQL como mecanismo de persistencia.

El despliegue se plantea inicialmente sobre una infraestructura gratuita, con Render o AWS como alternativas. La decisión definitiva del proveedor de infraestructura queda pendiente de documentarse mediante un ADR específico.

## 7.2. Corte vertical actualmente ejecutable

El corte vertical actualmente ejecutable corresponde al **backend de TAIA ejecutado como una única aplicación FastAPI**, desplegada localmente mediante Uvicorn.

Este corte integra los cuatro módulos actualmente implementados:

* **Usuario**
* **Academic**
* **AI**
* **Reminders**

La arquitectura mantiene un despliegue como **monolito modular**: los módulos se encuentran separados lógicamente dentro del código fuente, pero se ejecutan dentro del mismo proceso de aplicación.

### 7.2.1. Infraestructura de ejecución

El despliegue local actualmente utilizado puede representarse de la siguiente manera:

```text
┌──────────────────────────────────────────────────────────────┐
│                    Entorno de desarrollo                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  Proceso Python                        │  │
│  │                                                        │  │
│  │  Uvicorn                                               │  │
│  │    │                                                   │  │
│  │    ▼                                                   │  │
│  │  FastAPI                                               │  │
│  │    │                                                   │  │
│  │    ├──────────────► Usuario                            │  │
│  │    │                                                   │  │
│  │    ├──────────────► Academic                           │  │
│  │    │                                                   │  │
│  │    ├──────────────► AI                                 │  │
│  │    │                                                   │  │
│  │    └──────────────► Reminders                          │  │
│  │                                                        │  │
│  │  Persistencia temporal en memoria:                     │  │
│  │    • usuarios                                          │  │
│  │    • vínculos Telegram                                 │  │
│  │    • tareas académicas                                 │  │
│  │    • conversaciones AI                                 │  │
│  │    • recordatorios                                     │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                         │                                    │
│                         │ HTTP                               │
│                         ▼                                    │
│                 Cliente / Swagger                            │
└──────────────────────────────────────────────────────────────┘
```

El proceso puede iniciarse mediante:

```bash
uvicorn backend.app.main:app --reload
```

La API queda disponible localmente mediante HTTP, normalmente en:

```text
http://127.0.0.1:8000
```

y su documentación interactiva en:

```text
http://127.0.0.1:8000/docs
```

### 7.2.2. Mapeo de módulos al proceso de ejecución

Los cuatro módulos se ejecutan dentro del mismo proceso Python:

| Módulo        | Bloques desplegados                                                          | Infraestructura actual  |
| ------------- | ---------------------------------------------------------------------------- | ----------------------- |
| **Usuario**   | API, casos de uso, dominio, repositorios, JWT y servicios de contraseña      | Proceso FastAPI/Uvicorn |
| **Academic**  | API, casos de uso, dominio y repositorio de tareas                           | Proceso FastAPI/Uvicorn |
| **AI**        | API, casos de uso, conversación, gateway académico y adaptador LLM           | Proceso FastAPI/Uvicorn |
| **Reminders** | Controller, casos de uso, dominio, repositorio y adaptadores de notificación | Proceso FastAPI/Uvicorn |

No existe actualmente un proceso independiente por módulo.

Esta decisión corresponde al estilo de **monolito modular** adoptado para el MVP.

### 7.2.3. Persistencia del corte actualmente ejecutable

El corte actual utiliza almacenamiento en memoria para permitir la ejecución local y las pruebas sin depender de una infraestructura de base de datos externa.

```text
FastAPI
   │
   ├── Usuario
   │      ├── InMemoryUserRepository
   │      └── InMemoryTelegramLinkRepository
   │
   ├── Academic
   │      └── InMemoryTaskRepository
   │
   ├── AI
   │      └── InMemoryConversationStore
   │
   └── Reminders
          └── InMemoryReminderRepository
```

Estas implementaciones son **volátiles**: los datos almacenados se pierden cuando se detiene o reinicia el proceso.

Por esta razón, este despliegue debe considerarse un **entorno de desarrollo y validación del corte vertical**, no todavía un despliegue productivo.

### 7.2.4. Dependencias externas

El backend contiene adaptadores preparados para comunicarse con servicios externos, pero estos no son necesarios para levantar y probar los recorridos internos principales.

| Dependencia          | Uso                         | Estado en el corte actual                                                          |
| -------------------- | --------------------------- | ---------------------------------------------------------------------------------- |
| **Gemini**           | Interpretación mediante LLM | Adaptador implementado; requiere configuración de credenciales para ejecución real |
| **Telegram Bot API** | Envío de notificaciones     | Adaptador implementado; requiere token del bot y vinculación de Telegram           |
| **PostgreSQL**       | Persistencia definitiva     | Previsto; no utilizado por el corte actual                                         |
| **Flutter**          | Cliente móvil               | Previsto; el backend puede probarse actualmente mediante Swagger/HTTP              |

La ausencia de Gemini o Telegram no impide iniciar el backend. Las funcionalidades que dependan directamente de estos servicios requieren su respectiva configuración.

### 7.2.5. Corte vertical funcional actualmente demostrable

El despliegue actual permite ejecutar y probar directamente mediante HTTP los siguientes recorridos:

```text
                         ┌──────────────┐
                         │   Usuario    │
                         │              │
                         │ registro     │
                         │ login        │
                         │ JWT          │
                         └──────┬───────┘
                                │
                         user_id autenticado
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
      ┌────────────┐     ┌────────────┐     ┌────────────┐
      │ Academic   │     │     AI     │     │ Reminders  │
      │            │     │            │     │            │
      │ tareas     │◄────│ gateway    │     │ reminders  │
      │            │     │            │────►│            │
      └─────┬──────┘     └────────────┘     └─────┬──────┘
            │                                     │
            ▼                                     ▼
     InMemoryTaskRepository             InMemoryReminderRepository
                                                   │
                                                   ▼
                                         Telegram Adapter*
```

`*` El envío efectivo hacia Telegram requiere la configuración del bot.

En consecuencia, el corte vertical actualmente ejecutable **ya no se limita al módulo Academic**. La infraestructura local permite levantar conjuntamente los cuatro módulos y probar sus interfaces HTTP y sus integraciones internas.

### 7.2.6. Integración interna entre módulos

La comunicación entre módulos ocurre dentro del mismo proceso y no mediante HTTP interno.

Las principales relaciones son:

```text
Usuario
   │
   └──► autenticación / user_id
          │
          ├────────► Academic
          │
          ├────────► AI
          │
          └────────► Reminders


AI
 │
 └──► AcademicGateway
          │
          └──► Academic


Reminders
 │
 └──► AcademicTaskLookup
          │
          └──► Academic
```

Este diseño evita introducir complejidad de red innecesaria dentro del monolito.

Los límites entre módulos se mantienen mediante **puertos, adaptadores y casos de uso**, mientras que el proceso de despliegue continúa siendo único.

### 7.2.7. Pruebas del despliegue actual

El corte vertical se valida mediante la suite automatizada del proyecto.

El estado actual registrado para esta versión es:

```text
74 passed
```

Las pruebas cubren los principales recorridos implementados de:

* autenticación;
* gestión académica;
* integración AI–Academic;
* gestión de recordatorios;
* aislamiento entre usuarios;
* notificaciones y adaptadores de Telegram.

La suite permite validar el comportamiento de los módulos sin requerir PostgreSQL, Gemini ni Telegram para los escenarios que no dependen directamente de estos servicios.

### 7.2.8. Límites del despliegue actual

El despliegue descrito no debe interpretarse como la arquitectura productiva definitiva.

Actualmente quedan fuera de este corte:

* persistencia permanente mediante PostgreSQL;
* despliegue distribuido o mediante contenedores;
* scheduler persistente para ejecutar automáticamente los recordatorios al llegar `scheduled_at`;
* aplicación Flutter integrada como cliente;
* configuración productiva de Gemini;
* configuración productiva del bot de Telegram;
* mecanismos de observabilidad y operación propios de producción.

La infraestructura actual tiene como objetivo **permitir la ejecución, integración y validación del MVP en un entorno local**, manteniendo la estructura modular necesaria para evolucionar posteriormente hacia una infraestructura productiva.

### 7.2.9. Evolución prevista del despliegue

La evolución prevista conserva los módulos dentro de un único backend inicialmente:

```text
                    Producción futura
                           │
                 ┌─────────▼─────────┐
                 │   TAIA Backend    │
                 │   FastAPI         │
                 │                   │
                 │ Usuario           │
                 │ Academic          │
                 │ AI                │
                 │ Reminders         │
                 └───────┬───────────┘
                         │
             ┌───────────┼──────────────┐
             │           │              │
             ▼           ▼              ▼
        PostgreSQL    Gemini       Telegram
```

La sustitución de los repositorios en memoria por PostgreSQL y la activación de los adaptadores externos permitirá evolucionar desde el corte local actual hacia un despliegue persistente.

No se contempla como objetivo inmediato separar los cuatro módulos en microservicios. La decisión actual mantiene un **monolito modular** para reducir la complejidad operacional durante el desarrollo del MVP.


## 7.3. Restricciones de despliegue

El despliegue debe respetar las siguientes restricciones:

* El backend debe poder ejecutarse con infraestructura gratuita durante el desarrollo académico.
* Las credenciales y secretos de servicios externos no deben almacenarse en el repositorio.
* La persistencia definitiva debe quedar aislada mediante `TaskRepository`, permitiendo reemplazar el repositorio en memoria por PostgreSQL.
* El proveedor de LLM debe permanecer aislado mediante un adaptador para facilitar su sustitución.
* La arquitectura debe considerar que una infraestructura gratuita puede suspender procesos por inactividad, especialmente para las funcionalidades de notificación programada.
* El backend debe ser el punto de control de acceso a los datos académicos; los servicios externos no acceden directamente a la base de datos.