---
date: august 2026
title: "![arc42](images/arc42-logo.png) Template"
---

# 1. Introduction and Goals {#section-introduction-and-goals}

TAIA (Task Artificial Intelligence Assistant) es un asistente académico para
estudiantes universitarios. Ofrece dos canales de entrada —un bot de Telegram y
una aplicación móvil Flutter— sobre un backend compartido.

El problema tiene dos caras. La primera es la **fricción de captura**: el
estudiante se entera de una tarea justo cuando no puede detenerse a llenar un
formulario —en clase, saliendo del salón, leyendo un chat de grupo—, y el
formulario exige tiempo, atención y manos libres. Cuando faltan, la tarea no se
registra y se olvida. TAIA permite registrarla escribiendo una frase suelta en
Telegram, un canal que el estudiante ya tiene abierto. La segunda es la
**organización y el hábito**: registrar no basta, porque el estudiante también
necesita distribuir su tiempo de estudio y sostener la constancia. TAIA usa un
modelo de lenguaje (LLM) para proponer horarios compatibles con el horario de
clases, entre los cuales el estudiante elige.

Frente a Google Calendar, Notion o un bot de recordatorios genérico, el
diferenciador es la combinación de captura conversacional sin formulario,
interpretación automática del lenguaje natural y planificación proactiva del
tiempo de estudio: las herramientas existentes o exigen estructura manual o no
planifican. La identidad visual del sistema es un pulpo: muchos brazos, muchas
tareas atendidas a la vez.

## 1.1. Requirements Overview {#_requirements_overview}

El sistema recibe mensajes en lenguaje natural, los interpreta mediante un LLM,
extrae los campos de una tarea académica, pide confirmación al usuario y los
persiste. A partir de ahí notifica las tareas próximas a vencer y propone planes
de estudio; la misma información es consultable desde la aplicación móvil.

El público inicial son los estudiantes de nuestra universidad, con la intención
de extender el sistema a otras. El volumen esperado en la primera etapa es de
**decenas de usuarios activos**, con picos en la mañana y en la noche.

| ID | Requisito | Horizonte |
|---|---|---|
| RF-01 | El sistema debe permitir registrar información académica mediante lenguaje natural | MVP |
| RF-02 | El sistema debe permitir consultar la información académica propia del estudiante | MVP |
| RF-03 | El sistema debe interpretar solicitudes del estudiante mediante un servicio de inteligencia artificial | MVP |
| RF-04 | El sistema debe validar la información interpretada antes de almacenarla | MVP |
| RF-05 | El sistema debe generar y entregar recordatorios asociados a la información académica registrada | MVP |
| RF-06 | El sistema debe mantener aislada la información académica de cada estudiante | MVP |
| RF-07 | El sistema debe permitir la interacción mediante Telegram y la aplicación cliente | MVP |
| RF-08 | Sistema de recompensas por constancia (árbol que crece con las sesiones completadas) | Deseable, posterior al MVP |

RF-08 es **deseable, no comprometido**: se abordará después del MVP y su
ausencia no invalida el producto. RF-10 está **fuera del alcance actual**; se
contempla como evolución y solo se abordará si el tiempo lo permite, por lo que
no condiciona el diseño del MVP.

El primer corte vertical es el aspecto **A-01**, que realiza RF-01: mensaje en
Telegram → interpretación con el LLM → confirmación del usuario → persistencia
en PostgreSQL → visualización en la aplicación. A-01 atraviesa todas las capas y
sirve de base para el resto de la construcción.

## 1.2. Quality Goals {#_quality_goals}

Los objetivos de calidad de TAIA se priorizan de acuerdo con su impacto sobre la utilidad del sistema y el riesgo técnico asociado.

| Priority | Quality Goal | Description | Related Scenario |
|---|---|---|---|
| 1 | **Seguridad y privacidad** | Garantizar que cada estudiante pueda acceder únicamente a su propia información académica y que los intentos de acceso no autorizado sean rechazados. | S4 — Acceso únicamente a datos del propio estudiante |
| 2 | **Exactitud** | Garantizar que la información académica expresada en lenguaje natural sea interpretada y registrada correctamente. | S1 — Registro correcto de información académica |
| 3 | **Puntualidad** | Garantizar que los recordatorios académicos sean entregados cerca de la hora programada. | S2 — Entrega puntual de recordatorios |
| 4 | **Rendimiento** | Mantener tiempos de respuesta adecuados para las interacciones con el asistente. | S3 — Respuesta del asistente ante un mensaje |
| 5 | **Mantenibilidad** | Permitir la sustitución del proveedor o modelo de IA sin modificar la lógica de negocio principal ni la persistencia del sistema. | S5 — Sustitución del modelo de IA |

Los objetivos se consideran prioritarios porque TAIA gestiona información académica personal, depende de servicios externos para la interpretación mediante IA y requiere ofrecer una interacción suficientemente rápida y confiable para resultar útil al estudiante.

## 1.3. Stakeholders {#_stakeholders}

| Rol | Quién | Expectativa |
|---|---|---|
| Estudiante usuario | Estudiantes de la universidad; a futuro, de otras universidades | Registrar tareas sin fricción, recibir recordatorios fiables y obtener un plan de estudio realista |
| Equipo de desarrollo | Luis Mendoza, Deiner Gonzales, Valeria Berrio, Mark Pastrana | Una arquitectura comprensible y documentada que puedan construir entre cuatro personas dentro del plazo del curso |
| Docente evaluador | Profesor del curso de Arquitectura de Software | Documentación arquitectónica trazable (requisito → C4 → ADR → código → pruebas → evidencia) y uso de IA registrado |

# 2. Architecture Constraints {#section-architecture-constraints}

Para cada restricción se indica su implicación arquitectónica: qué obliga o qué
prohíbe al construir el sistema.

**Restricciones técnicas**

| Restricción | Implicación arquitectónica |
|---|---|
| Stack definido: Flutter (cliente móvil), FastAPI (backend), PostgreSQL (persistencia), Telegram Bot API (canal conversacional y de notificación) y Gemini (proveedor LLM actual) | La elección tecnológica no está en discusión; el diseño se concentra en repartir responsabilidades entre esas piezas, no en sustituirlas |
| Plataforma objetivo: **Android** | iOS y web quedan fuera de esta etapa; no se invierte esfuerzo en abstracciones multiplataforma más allá de lo que Flutter ofrece por defecto |
| El proveedor de LLM debe ser **intercambiable** | El sistema depende de una interfaz propia (puerto) y el SDK del proveedor queda aislado tras un adaptador; ningún otro componente puede acoplarse a Gemini directamente |
| **Costo cero**: toda la infraestructura opera dentro de capas gratuitas | Impone tres límites duros: cuotas de peticiones y tokens del LLM, que obligan a controlar el tamaño del contexto enviado; límites de almacenamiento y conexiones de la base de datos; y un hosting que puede suspender el proceso por inactividad, lo cual afecta a las notificaciones programadas (RF-05) y obliga a un disparo que no dependa de un proceso siempre activo |
| Despliegue previsto en Render o en la capa gratuita de AWS | La decisión no está cerrada y se documentará en un ADR; hasta entonces el diseño evita depender de servicios propios de un proveedor concreto |
| El canal de registro depende de un tercero (Telegram) | El equipo no controla su disponibilidad ni sus políticas. La aplicación Flutter debe permitir registrar y consultar tareas por sí sola (RF-04), de modo que una caída de Telegram degrade el sistema en lugar de inutilizarlo |

**Restricciones organizacionales**

| Restricción | Implicación arquitectónica |
|---|---|
| Equipo de cuatro personas, sin dedicación completa, dentro del calendario académico del curso | Favorece soluciones simples y comprensibles por todo el equipo frente a soluciones óptimas pero costosas de construir |
| El proyecto se desarrolla por **aspectos**: cortes verticales trazados en `docs/aspectos.md` con la cadena Requisito → C4 → ADR → Código → Pruebas → Evidencia | Cada incremento atraviesa todas las capas y deja trazabilidad completa; no se construyen capas horizontales aisladas |
| **Registro obligatorio del uso de IA** en `docs/ia.md`, con el formato de entrada numerada exigido por el curso | Todo uso significativo de IA en el desarrollo queda documentado, revisado y verificado por el equipo |
| Entregables y fechas definidos por el curso | No se documentan fechas concretas por no estar confirmadas; se añadirán cuando el equipo las fije |

**Restricciones legales**

| Restricción | Implicación arquitectónica |
|---|---|
| El sistema debe cumplir con las obligaciones aplicables de protección de datos personales sobre la información académica asociada a cada estudiante | La arquitectura debe limitar el acceso a los datos al usuario correspondiente, evitar la exposición innecesaria de información personal y mantener mecanismos de control que permitan proteger los datos almacenados y transmitidos |

**Convenciones**

| Convención | Implicación arquitectónica |
|---|---|
| Documentación del proyecto en español | Se redacta en español con independencia del idioma de las plantillas empleadas |
| Documentación arquitectónica siguiendo **arc42 v9.0**, escrita dentro de `docs/arc42/arc42-template-EN.md` | Se conservan los encabezados originales en inglés y la numeración de la plantilla |
| Diagramas siguiendo el **modelo C4** | Las vistas de contexto, contenedores y componentes se expresan en los niveles de C4 y se enlazan desde el aspecto correspondiente |
| Decisiones arquitectónicas registradas como **ADR** | Toda decisión estructural —proveedor de LLM, plataforma de despliegue, mecanismo de notificaciones— se documenta como ADR enlazado desde `docs/aspectos.md` |
| Código, identificadores y mensajes de commit en inglés; comentarios y documentación en español | Convención propuesta, aún no fijada por el equipo |
| `README.md` está codificado en UTF-16 LE; el resto del repositorio en UTF-8 | Las herramientas y scripts que procesen el repositorio deben contemplar esa diferencia |

# 3. Context and Scope {#section-context-and-scope}

## 3.1. Business Context {#_business_context}
TAIA se sitúa entre el estudiante y los servicios necesarios para gestionar su información académica.

El estudiante utiliza TAIA para **registrar y consultar información académica**, así como para **recibir recordatorios**. TAIA interpreta las solicitudes expresadas en lenguaje natural, procesa las operaciones correspondientes y mantiene la información asociada al estudiante.

### Intercambio principal

```text
+------------------+
|    Estudiante    |
+--------+---------+
         |
         | registra / consulta información
         | y recibe recordatorios
         v
+--------------------------+
|           TAIA           |
| Task Artificial          |
| Intelligence Assistant   |
+-----------+--------------+
            |
            | interpretación de lenguaje natural
            v
+--------------------------+
| Servicio de IA (Gemini)  |
+--------------------------+

TAIA <----> Telegram
        mensajes y recordatorios
```

### Interfaces externas del contexto de negocio

| Sistema / Actor | Relación con TAIA |
|---|---|
| **Estudiante** | Utiliza TAIA para registrar y consultar información académica y recibir recordatorios. |
| **Telegram** | Proporciona un canal conversacional para recibir mensajes del estudiante y enviar respuestas y recordatorios. |
| **Servicio de IA (Gemini)** | Proporciona la interpretación de solicitudes expresadas mediante lenguaje natural. |

---

## 3.2. Technical Context {#_technical_context}

TAIA se integra con servicios externos mediante interfaces tecnológicas específicas. El backend actúa como punto central de procesamiento y validación de las solicitudes.

### Interfaces técnicas

| Sistema / Interfaz | Tecnología / Canal | Propósito |
|---|---|---|
| **Aplicación cliente** | Flutter / HTTP | Permitir al estudiante interactuar con las funcionalidades de TAIA. |
| **Telegram** | Telegram Bot API / Webhook | Recibir mensajes del estudiante y enviar respuestas y recordatorios. |
| **Servicio de IA** | API de Gemini / HTTP | Interpretar solicitudes expresadas en lenguaje natural y producir información estructurada para su posterior validación. |
| **Persistencia** | PostgreSQL / conexión de base de datos | Almacenar y consultar la información académica gestionada por TAIA. |

### Flujo técnico principal

```text
                         Estudiante
                         /        \
                        /          \
                       v            v
                   Flutter       Telegram
                       |            |
                       |            |
                       +-----+------+
                             |
                             | HTTP / Webhook
                             v
                      +-------------+
                      |   FastAPI   |
                      |   Backend   |
                      +------+------+
                             |
                   +---------+---------+
                   |                   |
                   v                   v
              Gemini API          PostgreSQL
                   |
                   v
          Interpretación
           estructurada
                   |
                   v
        Validación y reglas
          de negocio en TAIA
```

> **Nota:** El servicio de IA se utiliza únicamente como mecanismo de interpretación y **no está autorizado para acceder directamente a la persistencia**.

---

**\<Mapping Input/Output to Channels\>**


| Entrada / Salida | Canal | Uso |
|---|---|---|
| **Mensaje del estudiante** | Telegram Bot API | Entrada de solicitudes expresadas en lenguaje natural. |
| **Solicitud desde la aplicación** | HTTP hacia FastAPI | Entrada de operaciones académicas desde el cliente Flutter. |
| **Respuesta del asistente** | Telegram / aplicación cliente | Confirmación, resultado de una operación o respuesta a una consulta. |
| **Recordatorio académico** | Telegram y/o canal configurado | Entrega de información asociada a un evento programado. |
| **Información estructurada generada por IA** | API de Gemini → FastAPI | Resultado de interpretación que debe ser validado antes de utilizarse. |
| **Datos académicos persistidos** | PostgreSQL | Almacenamiento y consulta de la información gestionada por TAIA. |

---

## 3.3. Scope

El alcance del **MVP de TAIA** comprende la gestión de información académica básica:

- **Tareas**
- **Exámenes**
- **Materias**
- **Clases y eventos**
- Interacción mediante **lenguaje natural**
- Consulta de **información propia**
- Generación y entrega de **recordatorios**

### Fuera del alcance del MVP

Las capacidades avanzadas de inteligencia artificial quedan fuera del alcance de esta primera versión. Entre ellas se encuentran:

- RAG (*Retrieval-Augmented Generation*)
- Embeddings
- Búsqueda semántica
- Otras extensiones avanzadas de IA

Estas capacidades podrán incorporarse en **etapas posteriores** del proyecto.

# 4. Solution Strategy {#section-solution-strategy}

TAIA adopta un **monolito modular con organización hexagonal en los módulos que presentan dependencias externas relevantes**. Esta estrategia busca mantener una arquitectura sencilla para el MVP, evitando la complejidad operativa de una arquitectura distribuida, mientras establece límites que permitan evolucionar el sistema y sustituir dependencias externas cuando sea necesario.

## 4.1. Architectural Style

El sistema se implementará como un único monolito desplegable, dividido en módulos con responsabilidades claramente definidas.

Dentro de los módulos que interactúan con sistemas externos se utilizará el principio de **puertos y adaptadores**. Los puertos definirán las interfaces que necesita la lógica de negocio, mientras que los adaptadores contendrán los detalles específicos de tecnologías y proveedores externos.

Las principales dependencias externas consideradas son:

- Telegram Bot API como canal de comunicación.
- Gemini como proveedor inicial de inteligencia artificial.
- PostgreSQL como mecanismo de persistencia.

La lógica de negocio no dependerá directamente de las APIs concretas de estos proveedores cuando exista una probabilidad relevante de sustitución.

## 4.2. Architectural Principles

### Separación de responsabilidades

Cada módulo tendrá una responsabilidad definida y deberá evitar dependencias innecesarias sobre otros módulos.

### Aislamiento de dependencias externas

Las integraciones con servicios externos se realizarán mediante interfaces y adaptadores cuando su sustitución o evolución sea relevante para el sistema.

### Dominio independiente de infraestructura

Las reglas de negocio no deberán depender directamente de detalles de Telegram, Gemini o PostgreSQL.

### Validación antes de persistencia

La información interpretada por el servicio de inteligencia artificial deberá ser validada por el backend antes de modificar la información persistida.

### Seguridad por contexto de usuario

Las operaciones sobre información académica deberán ejecutarse dentro del contexto del estudiante correspondiente, evitando el acceso cruzado entre usuarios.

## 4.3. Quality-Driven Strategy

Las principales decisiones arquitectónicas se relacionan con los escenarios de calidad definidos para TAIA:

| Quality Goal | Estrategia arquitectónica |
|---|---|
| **S1 — Exactitud** | Separación entre interpretación de IA, validación y reglas de negocio antes de persistir información. |
| **S2 — Puntualidad** | Módulo de recordatorios separado de la lógica de interacción, permitiendo gestionar su programación y entrega de forma independiente. |
| **S3 — Rendimiento** | Mantener una arquitectura monolítica con comunicación interna directa y evitar complejidad distribuida innecesaria. |
| **S4 — Seguridad** | Centralizar las reglas de autorización y mantener el acceso a información académica dentro del contexto del estudiante. |
| **S5 — Mantenibilidad** | Utilizar puertos y adaptadores para aislar las dependencias externas, especialmente el proveedor de inteligencia artificial. |

## 4.4. Deployment Strategy

Durante esta etapa TAIA se mantendrá como una **única unidad desplegable**. Esta decisión reduce la complejidad operacional del MVP y evita introducir comunicación entre servicios, despliegues independientes y mecanismos de observabilidad distribuida que no son necesarios para el alcance actual.

La modularización interna permitirá evolucionar posteriormente partes específicas del sistema si el crecimiento del dominio, la carga o las necesidades de operación justifican una separación adicional.

# 5. Building Block View {#section-building-block-view}

## 5.1. Whitebox Overall System {#_whitebox_overall_system}

El backend de TAIA se organiza como un monolito modular. Para el primer corte vertical, correspondiente al aspecto A-01, se implementa el módulo académico mediante una organización hexagonal selectiva.

El objetivo de esta estructura es separar la entrada HTTP, los casos de uso, las reglas del dominio y los mecanismos de persistencia. De esta manera, la lógica de negocio no depende directamente de FastAPI ni de una tecnología concreta de persistencia.

### Vista general

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

### Contained Building Blocks

| Bloque                 | Responsabilidad                                                                        | Ubicación                                           |
| ---------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------- |
| API / Adapter          | Recibir solicitudes HTTP, transformar los datos de entrada y devolver respuestas HTTP. | `backend/app/modules/academic/adapters/`            |
| Application            | Ejecutar los casos de uso de TAIA y coordinar las operaciones necesarias.              | `backend/app/modules/academic/application/`         |
| Domain                 | Representar la información académica y aplicar las reglas propias del dominio.         | `backend/app/modules/academic/domain/`              |
| Repository Port        | Definir la abstracción que necesita la aplicación para almacenar y consultar tareas.   | `backend/app/modules/academic/application/ports.py` |
| InMemoryTaskRepository | Implementar el puerto de persistencia para el corte vertical actual.                   | `backend/app/modules/academic/adapters/`            |

### Important Interfaces

Las principales interfaces del módulo son:

* **API HTTP:** expone las operaciones de registro y consulta de tareas.
* **RegisterTaskUseCase:** representa el caso de uso de registro de una tarea.
* **ListTasksUseCase:** representa el caso de uso de consulta de tareas.
* **TaskRepository:** puerto mediante el cual los casos de uso acceden a la persistencia.

La interfaz `TaskRepository` es especialmente importante porque desacopla la aplicación del mecanismo concreto de almacenamiento.

## 5.2. API / Adapter {#_api_adapter}

### Responsabilidad

El adaptador de API recibe las solicitudes HTTP y las transforma en llamadas a los casos de uso del módulo académico.

No contiene las reglas principales del dominio. Su responsabilidad es actuar como frontera entre FastAPI y la aplicación.

### Interfaces

Expone endpoints HTTP para:

* Registrar una tarea.
* Consultar las tareas registradas.

### Ubicación

`backend/app/modules/academic/adapters/`

### Relación con requisitos

Contribuye al cumplimiento de **RF-01**, al proporcionar la entrada necesaria para el registro de información académica.

## 5.3. Application {#_application}

### Responsabilidad

La capa de aplicación contiene los casos de uso que coordinan las operaciones del módulo académico.

En el corte vertical actual se implementan:

* `RegisterTaskUseCase`
* `ListTasksUseCase`

Los casos de uso reciben información validada desde la interfaz, crean o consultan entidades del dominio y utilizan el puerto de persistencia correspondiente.

### Interfaces

La aplicación depende de `TaskRepository`, definido como puerto.

### Ubicación

`backend/app/modules/academic/application/`

### Relación con requisitos

Constituye el núcleo del recorrido correspondiente al aspecto **A-01** y al requisito **RF-01**.

## 5.4. Domain {#_domain}

### Responsabilidad

El dominio representa las entidades y reglas propias de la información académica gestionada por TAIA.

En el corte actual se utiliza la entidad `Task`, que representa una tarea académica registrada por el estudiante.

El dominio no depende directamente de FastAPI, PostgreSQL, Telegram ni Gemini.

### Ubicación

`backend/app/modules/academic/domain/`

### Características

El dominio valida las condiciones necesarias para crear una tarea válida y mantiene las reglas que deben cumplirse independientemente de la tecnología utilizada para recibir o almacenar la información.

## 5.5. Repository Port {#_repository_port}

### Responsabilidad

`TaskRepository` define las operaciones de persistencia requeridas por los casos de uso.

Este componente constituye el puerto de salida del módulo académico.

La aplicación depende de esta abstracción en lugar de conocer directamente el mecanismo utilizado para almacenar las tareas.

### Ubicación

`backend/app/modules/academic/application/ports.py`

### Importancia arquitectónica

Este puerto implementa el principio definido en el ADR-0001 de aislar las dependencias externas y mantener las reglas de negocio independientes de la infraestructura.

## 5.6. InMemoryTaskRepository {#_inmemory_task_repository}

### Responsabilidad

`InMemoryTaskRepository` proporciona la implementación de persistencia utilizada por el primer corte vertical.

Permite ejecutar y probar el recorrido completo sin introducir todavía la dependencia de una instancia de PostgreSQL.

### Ubicación

`backend/app/modules/academic/adapters/`

### Estado

Es una implementación temporal para el corte vertical actual.

En una siguiente evolución será posible incorporar un adaptador de PostgreSQL que implemente el mismo puerto `TaskRepository`.

### Relación con la arquitectura

El reemplazo del repositorio en memoria por PostgreSQL no debería requerir cambios en las reglas del dominio ni en los casos de uso, siempre que el nuevo adaptador respete el contrato definido por `TaskRepository`.

## 5.7. Límites del corte vertical

El corte vertical actual atraviesa los siguientes bloques:

```text
HTTP
  ↓
API / Adapter
  ↓
Application
  ↓
Domain
  ↓
TaskRepository
  ↓
InMemoryTaskRepository
```

Este recorrido constituye la implementación ejecutable actual de **A-01**.

Las integraciones con **Telegram**, **Gemini**, **PostgreSQL** y la aplicación **Flutter** forman parte de la arquitectura objetivo del sistema, pero no se consideran implementaciones completas dentro de este corte.

Por tanto, la documentación de esta sección distingue entre los bloques actualmente ejecutables y los componentes previstos para las siguientes iteraciones.

# 6. Runtime View {#section-runtime-view}

La vista de ejecución describe el recorrido de una solicitud dentro del corte vertical implementado para el aspecto **A-01 — Captura inteligente de información académica**.

El escenario seleccionado es el **registro de una tarea académica mediante la API HTTP**. Este recorrido permite demostrar que la solicitud atraviesa la interfaz, la lógica de aplicación, el dominio y la persistencia mediante el puerto definido por la arquitectura.

## 6.1. Escenario — Registro de una tarea

### Flujo de ejecución

```text
Estudiante / Cliente HTTP
          │
          │ POST /tasks
          ▼
┌─────────────────────┐
│ Academic API Adapter│
│     FastAPI         │
└──────────┬──────────┘
           │
           │ datos de la solicitud
           ▼
┌─────────────────────┐
│ RegisterTaskUseCase │
│    Application      │
└──────────┬──────────┘
           │
           │ crear tarea
           ▼
┌─────────────────────┐
│       Task          │
│       Domain        │
└──────────┬──────────┘
           │
           │ TaskRepository
           ▼
┌─────────────────────────┐
│ InMemoryTaskRepository  │
│       Adapter           │
└──────────┬──────────────┘
           │
           │ tarea almacenada
           ▼
       Respuesta HTTP
```

### Descripción del escenario

1. El cliente envía una solicitud HTTP para registrar una tarea.
2. El adaptador de API de FastAPI recibe la solicitud y transforma los datos de entrada al formato utilizado por la aplicación.
3. `RegisterTaskUseCase` ejecuta el caso de uso de registro.
4. El caso de uso crea una instancia válida de la entidad `Task`.
5. La aplicación utiliza el puerto `TaskRepository` para solicitar el almacenamiento de la tarea.
6. `InMemoryTaskRepository` implementa actualmente ese puerto y almacena la tarea.
7. El adaptador de API devuelve una respuesta HTTP indicando el resultado de la operación.

## 6.2. Escenario — Consulta de tareas

El segundo flujo implementado permite consultar las tareas registradas.

```text
Cliente HTTP
     │
     │ GET /tasks
     ▼
Academic API Adapter
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
Lista de tareas
     │
     ▼
Respuesta HTTP
```

El adaptador recibe la solicitud de consulta y delega la operación al `ListTasksUseCase`. Este utiliza el puerto `TaskRepository` para recuperar las tareas almacenadas y devuelve el resultado al adaptador, que lo transforma en una respuesta HTTP.

## 6.3. Manejo de validaciones

Durante el registro, los datos pasan por las reglas correspondientes del dominio antes de ser almacenados.

```text
Solicitud HTTP
      │
      ▼
API Adapter
      │
      ▼
RegisterTaskUseCase
      │
      ▼
Validación / creación de Task
      │
      ├──── Inválida ────► Error / respuesta HTTP
      │
      ▼
TaskRepository
      │
      ▼
Persistencia
```

De esta manera, una tarea que no cumple las condiciones definidas por el dominio no continúa hasta la persistencia.

## 6.4. Límites del escenario actual

El escenario descrito corresponde al **corte vertical ejecutable actual**.

Actualmente el flujo llega hasta `InMemoryTaskRepository`. PostgreSQL todavía no forma parte del recorrido ejecutable de este incremento.

De igual manera, la interpretación mediante Gemini y la captura mediante Telegram corresponden a integraciones previstas para las siguientes iteraciones. El corte actual utiliza una entrada HTTP para demostrar el recorrido extremo a extremo de la lógica implementada.

Esta delimitación permite validar primero la estructura interna del sistema y posteriormente sustituir o incorporar los adaptadores externos sin modificar el núcleo de la lógica de negocio.

## 6.5. Relación con pruebas

El escenario de registro se encuentra cubierto mediante pruebas automatizadas del módulo académico.

Las pruebas verifican el recorrido de la solicitud a través de la API y la ejecución del caso de uso hasta el repositorio utilizado por el corte vertical.

Esto permite comprobar que los bloques descritos en esta vista no son únicamente elementos documentales, sino componentes que participan en un flujo ejecutable del sistema.

# 7. Deployment View {#section-deployment-view}

## Infrastructure Level 1 {#_infrastructure_level_1}

***\<Overview Diagram\>***

Motivation

:   *\<explanation in text form\>*

Quality and/or Performance Features

:   *\<explanation in text form\>*

Mapping of Building Blocks to Infrastructure

:   *\<description of the mapping\>*

## Infrastructure Level 2 {#_infrastructure_level_2}

### *\<Infrastructure Element 1\>* {#_infrastructure_element_1}

*\<diagram + explanation\>*

### *\<Infrastructure Element 2\>* {#_infrastructure_element_2}

*\<diagram + explanation\>*

...​

### *\<Infrastructure Element n\>* {#_infrastructure_element_n}

*\<diagram + explanation\>*

# 8. Cross-cutting Concepts {#section-concepts}

## *\<Concept 1\>* {#_concept_1}

*\<explanation\>*

## *\<Concept 2\>* {#_concept_2}

*\<explanation\>*

...​

## *\<Concept n\>* {#_concept_n}

*\<explanation\>*

# 9. Architecture Decisions {#section-architecture-decisions}

Las decisiones arquitectónicas relevantes de TAIA se documentan mediante ADR (Architecture Decision Records). Los ADR contienen el contexto, las alternativas consideradas, la decisión adoptada y sus consecuencias.

## 9.1. ADR-0001 — Monolito modular con organización hexagonal selectiva

**Estado:** Aceptado

**Decisión:** TAIA utilizará un **monolito modular con organización hexagonal selectiva en los módulos que presentan dependencias externas relevantes**.

La aplicación se mantendrá como un único sistema desplegable durante el MVP, evitando la complejidad operativa de una arquitectura distribuida. Dentro de los módulos donde exista una dependencia externa susceptible de cambio se utilizarán puertos y adaptadores para reducir el acoplamiento.

La decisión se aplica especialmente a las integraciones con:

* Gemini, como proveedor de inteligencia artificial.
* Telegram, como canal conversacional y de notificaciones.
* PostgreSQL, como mecanismo de persistencia.

En el corte vertical actual, esta decisión se refleja en el módulo académico mediante la separación entre `application`, `domain` y `adapters`, así como mediante el puerto `TaskRepository` y su implementación `InMemoryTaskRepository`.

**Motivación:** La arquitectura debe mantener la simplicidad necesaria para el MVP y, al mismo tiempo, permitir sustituir dependencias externas sin modificar las reglas de negocio.

**Relación con requisitos y calidad:** La decisión contribuye principalmente a **S5 — Sustitución del modelo de IA**, escenario de calidad relacionado con la mantenibilidad y la independencia del proveedor.

**ADR relacionado:**
[ADR-0001 — Monolito modular con organización hexagonal selectiva](../adr/0001-estilo-arquitectonico.md)

## 9.2. Decisiones pendientes

Las decisiones sobre la implementación concreta de algunos mecanismos de infraestructura se documentarán mediante nuevos ADR cuando sean necesarias.

Entre ellas se encuentra la selección definitiva del mecanismo de despliegue y la implementación de los adaptadores concretos para PostgreSQL, Telegram y Gemini.

Estos elementos no forman parte del recorrido ejecutable del corte vertical actual y, por tanto, no se presentan como decisiones ya implementadas.

# 10. Quality Requirements {#section-quality-requirements}

Los requisitos de calidad de TAIA se expresan mediante escenarios medibles. Estos escenarios permiten evaluar el comportamiento esperado del sistema y sirven como referencia para las decisiones arquitectónicas y las pruebas.

## 10.1. Quality Tree

La utilidad del sistema se descompone en las siguientes características de calidad:

```text
UTILIDAD
│
├── Exactitud
│   │
│   └── Interpretación correcta de información académica
│       │
│       └── S1. Registro correcto de información académica
│
├── Disponibilidad / Puntualidad
│   │
│   └── Entrega oportuna de información
│       │
│       └── S2. Entrega puntual de recordatorios
│
├── Rendimiento
│   │
│   └── Tiempo de respuesta del asistente
│       │
│       └── S3. Respuesta del asistente ante un mensaje
│
├── Seguridad
│   │
│   └── Confidencialidad y aislamiento de información
│       │
│       └── S4. Acceso únicamente a datos del propio estudiante
│
└── Mantenibilidad
    │
    └── Independencia del proveedor de IA
        │
        └── S5. Sustitución del modelo de IA
```

## 10.2. Escenarios de calidad

### S1 — Registro correcto de información académica

**Fuente:** El estudiante.

**Estímulo:** Escribe en lenguaje natural información correspondiente a una tarea, examen, materia o clase/evento.

**Artefacto:** Servicio que interpreta el mensaje con el LLM y registro de TAIA.

**Entorno:** Sistema desplegado, con el servicio de IA disponible.

**Respuesta:** TAIA identifica los campos relevantes, solicita confirmación cuando corresponda y registra la información correctamente en PostgreSQL.

**Medida:** Al menos el 90 % de los campos esperados deben ser identificados y registrados correctamente en una muestra de 100 mensajes académicos representativos.

**Restricción relacionada:** El contexto enviado al LLM debe mantenerse controlado debido a las cuotas gratuitas disponibles.

**Justificación:** La captura sin fricción es una característica diferenciadora de TAIA. Una baja exactitud en la interpretación reduciría la confianza del estudiante en el sistema.

### S2 — Entrega puntual de recordatorios

**Fuente:** Sistema de TAIA.

**Estímulo:** Llega el momento programado para un recordatorio.

**Artefacto:** Servicio de recordatorios y notificaciones.

**Entorno:** Sistema desplegado y operativo.

**Respuesta:** TAIA envía el recordatorio al canal configurado por el estudiante.

**Medida:** Al menos el 95 % de los recordatorios deben ser entregados dentro de un margen de ±1 minuto respecto a la hora programada, en una prueba de 100 recordatorios.

**Justificación:** Los recordatorios solo son útiles si se entregan en el momento esperado por el estudiante.

### S3 — Respuesta del asistente ante un mensaje

**Fuente:** El estudiante.

**Estímulo:** El estudiante envía una consulta o instrucción válida al asistente de TAIA.

**Artefacto:** Backend de TAIA y servicio de interpretación mediante LLM.

**Entorno:** Sistema desplegado, con backend, Telegram y servicio de IA disponibles.

**Respuesta:** TAIA procesa el mensaje y devuelve una respuesta al estudiante.

**Medida:** El 95 % de las solicitudes deberá recibir una respuesta en un tiempo ≤ 7 segundos, medido desde la recepción del mensaje por el backend hasta el envío de la respuesta al canal del estudiante, bajo condiciones normales de operación.

**Restricción relacionada:** El sistema utiliza infraestructura gratuita, sin garantía de recursos dedicados, por lo que pueden existir arranques en frío y recursos compartidos.

**Justificación:** Un tiempo de respuesta excesivo afecta la usabilidad del asistente y puede perjudicar los escenarios de registro y consulta.

### S4 — Acceso únicamente a datos del propio estudiante

**Fuente:** El estudiante autenticado.

**Estímulo:** Envía un mensaje solicitando, directa o indirectamente, información perteneciente a otro estudiante.

**Artefacto:** Capa que construye el contexto para el LLM y mecanismo de persistencia.

**Entorno:** Sistema desplegado con múltiples estudiantes registrados.

**Respuesta:** TAIA devuelve únicamente información asociada al estudiante autenticado y rechaza cualquier intento de acceder a información perteneciente a otro estudiante.

**Medida:** En una prueba de 100 intentos de acceso, incluyendo solicitudes legítimas y solicitudes que intenten consultar información perteneciente a otros estudiantes, el sistema deberá permitir únicamente los accesos autorizados y rechazar el 100 % de los intentos no autorizados, sin exponer datos de otros usuarios.

**Restricción relacionada:** El uso de un LLM con contexto generado para cada petición exige controlar explícitamente el aislamiento de los datos.

**Justificación:** TAIA manejará información académica de estudiantes. Una fuga de información entre usuarios afectaría gravemente la seguridad y la confianza en el sistema.

### S5 — Sustitución del modelo de IA

**Fuente:** El equipo de desarrollo.

**Estímulo:** El proveedor o modelo de inteligencia artificial utilizado por TAIA deja de estar disponible, cambia sus condiciones de uso o se requiere migrar a otro proveedor.

**Artefacto:** Componente de integración con el LLM.

**Entorno:** Durante el mantenimiento y evolución del sistema.

**Respuesta:** El sistema debe permitir sustituir el proveedor de IA mediante el cambio o incorporación del adaptador correspondiente, manteniendo sin modificaciones las reglas de negocio y la interfaz utilizada por la aplicación.

**Medida:** La sustitución del proveedor de IA deberá requerir cambios en máximo 2 archivos del adaptador, sin modificar archivos pertenecientes al dominio ni a las reglas de negocio.

**Restricción relacionada:** El proveedor de LLM debe ser intercambiable.

**Justificación:** Los proveedores pueden modificar sus modelos, cuotas o condiciones de uso. El aislamiento del proveedor evita que un cambio de infraestructura obligue a modificar la lógica de negocio de TAIA.

## 10.3. Priorización de escenarios

| Escenario                      | Impacto | Riesgo técnico | Prioridad |
| ------------------------------ | ------- | -------------- | --------- |
| S1 — Registro correcto         | Alto    | Alto           | Alta      |
| S2 — Recordatorios puntuales   | Alto    | Alto           | Alta      |
| S3 — Respuesta del asistente   | Alto    | Media/Alta     | Alta      |
| S4 — Aislamiento de datos      | Alto    | Crítico        | Crítica   |
| S5 — Sustitución del modelo IA | Medio   | Medio          | Media     |

## 10.4. Relación con las decisiones arquitectónicas

Los escenarios de calidad sirven como fundamento para las decisiones arquitectónicas de TAIA.

En particular:

* **S1** influye en la separación entre interpretación, validación y reglas de dominio.
* **S2** influye en la separación del mecanismo de notificaciones respecto de la lógica de negocio.
* **S3** establece un objetivo de rendimiento condicionado por el uso de servicios externos y la infraestructura disponible.
* **S4** exige mantener el aislamiento de la información de cada estudiante y controlar el contexto utilizado por el sistema.
* **S5** motiva directamente el **ADR-0001**, que establece el uso de puertos y adaptadores para aislar las dependencias externas.

**ADR relacionado:** [ADR-0001 — Monolito modular con organización hexagonal selectiva](../adr/0001-estilo-arquitectonico.md)

# 11. Risks and Technical Debts {#section-technical-risks}

# 12. Glossary {#section-glossary}

| Término                         | Definición                                                                                                                                                                                                               |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **TAIA**                        | *Task Artificial Intelligence Assistant*. Asistente académico inteligente del proyecto que permite registrar y consultar información académica mediante lenguaje natural y diferentes canales de interacción.            |
| **Estudiante**                  | Usuario principal de TAIA. Registra tareas e información académica, consulta sus datos y recibe recordatorios.                                                                                                           |
| **Tarea (Task)**                | Unidad de información académica que representa una actividad que debe realizar el estudiante y que puede incluir datos como título y fecha de entrega.                                                                   |
| **A-01**                        | Aspecto del sistema correspondiente a la **Captura inteligente de información académica**. Constituye el primer corte vertical del proyecto.                                                                             |
| **Corte vertical**              | Incremento funcional que atraviesa diferentes partes de la arquitectura, desde una interfaz de entrada hasta la lógica de aplicación, el dominio y la persistencia, permitiendo ejecutar y probar un recorrido completo. |
| **Módulo académico (Academic)** | Módulo del backend encargado de las funcionalidades relacionadas con la gestión de información académica. En el corte actual contiene la funcionalidad de registro y consulta de tareas.                                 |
| **Dominio**                     | Parte de la arquitectura que representa las entidades y reglas propias del problema, independientemente de tecnologías externas.                                                                                         |
| **Caso de uso (Use Case)**      | Componente de la capa de aplicación que representa una operación que el sistema puede ejecutar. En el corte actual se incluyen `RegisterTaskUseCase` y `ListTasksUseCase`.                                               |
| **Puerto (Port)**               | Interfaz que define una dependencia requerida por la aplicación sin acoplarla a una implementación concreta. En el corte actual, `TaskRepository` define el puerto de persistencia.                                      |
| **Adaptador (Adapter)**         | Componente que conecta el núcleo de la aplicación con una tecnología o mecanismo externo mediante un puerto.                                                                                                             |
| **TaskRepository**              | Puerto de persistencia utilizado por los casos de uso para almacenar y consultar tareas sin depender de una implementación concreta.                                                                                     |
| **InMemoryTaskRepository**      | Adaptador de persistencia utilizado en el corte vertical actual. Almacena las tareas en memoria y permite ejecutar las pruebas sin depender todavía de PostgreSQL.                                                       |
| **API**                         | Interfaz mediante la cual otros componentes pueden comunicarse con TAIA. En el corte actual corresponde a la API HTTP implementada con FastAPI.                                                                          |
| **FastAPI**                     | Framework utilizado para implementar la API HTTP del backend de TAIA.                                                                                                                                                    |
| **Flutter**                     | Tecnología prevista para la aplicación móvil de TAIA. Forma parte de la arquitectura objetivo, pero no está implementada en el corte vertical actual.                                                                    |
| **Telegram**                    | Canal externo previsto para la captura conversacional de información y el envío de notificaciones al estudiante.                                                                                                         |
| **Gemini**                      | Proveedor de modelo de lenguaje utilizado como dependencia externa prevista para interpretar mensajes en lenguaje natural.                                                                                               |
| **PostgreSQL**                  | Sistema de gestión de base de datos previsto para la persistencia de la información académica de TAIA.                                                                                                                   |
| **LLM**                         | *Large Language Model*. Modelo de lenguaje utilizado por TAIA para interpretar mensajes en lenguaje natural y extraer información estructurada.                                                                          |
| **ADR**                         | *Architecture Decision Record*. Registro utilizado para documentar una decisión arquitectónica, su contexto, alternativas y consecuencias.                                                                               |
| **C4**                          | Modelo de documentación de arquitectura utilizado para representar el sistema mediante diferentes niveles de abstracción, incluyendo contexto y contenedores.                                                            |
| **arc42**                       | Plantilla utilizada para documentar la arquitectura de software de TAIA.                                                                                                                                                 |
