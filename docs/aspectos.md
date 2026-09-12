# Aspectos del sistema

| ID   | Aspecto                                               | Requisito                                | C4                                         | ADR                                           | Código                                                                                                                                     | Pruebas                                                                                                                                                                                                                                   | Evidencia                                                                                       |
| ---- | ----------------------------------------------------- | ---------------------------------------- | ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| A-01 | Captura inteligente de información académica          | RF-01, RF-02                             | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/academic/`](../backend/app/modules/academic/)                                                                        | [`test_academic_task_domain.py`](../backend/tests/test_academic_task_domain.py), [`test_academic_register_task.py`](../backend/tests/test_academic_register_task.py)                                                                      | [Prueba del corte vertical](../backend/tests/test_academic_register_task.py)                    |
| A-02 | Usuarios y autenticación                              | RF-06, RF-07                             | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/usuario/`](../backend/app/modules/usuario/)                                                                          | [`test_usuario_api.py`](../backend/tests/test_usuario_api.py)                                                                                                                                                                             | [Pruebas de registro, autenticación y acceso autenticado](../backend/tests/test_usuario_api.py) |
| A-03 | Asistente inteligente e interpretación de solicitudes | RF-01, RF-03, RF-04                      | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/ai/`](../backend/app/modules/ai/), [`backend/app/modules/academic/`](../backend/app/modules/academic/)               | [`test_ai_academic_gateway.py`](../backend/tests/test_ai_academic_gateway.py), [`test_ai_api.py`](../backend/tests/test_ai_api.py)                                                                                                        | [Pruebas del gateway académico y API de IA](../backend/tests/test_ai_academic_gateway.py)       |
| A-04 | Recordatorios y notificaciones                        | RF-05, RF-07                             | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/reminders/`](../backend/app/modules/reminders/), [`backend/app/modules/usuario/`](../backend/app/modules/usuario/)   | [`test_reminders_api.py`](../backend/tests/test_reminders_api.py), [`test_reminders_notifications.py`](../backend/tests/test_reminders_notifications.py), [`test_reminders_notify_api.py`](../backend/tests/test_reminders_notify_api.py) | [Pruebas de CRUD y notificación por Telegram](../backend/tests/test_reminders_notify_api.py)    |
| A-05 | Integración y aislamiento entre módulos               | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06 | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/`](../backend/app/modules/)                                                                                          | [`backend/tests/`](../backend/tests/)                                                                                                                                                                                                     | [Suite automatizada de integración y aislamiento](../backend/tests/)                            |
| A-06 | Persistencia y evolución de infraestructura           | RF-01, RF-02, RF-05                      | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/academic/`](../backend/app/modules/academic/), [`backend/app/modules/reminders/`](../backend/app/modules/reminders/) | [`test_academic_register_task.py`](../backend/tests/test_academic_register_task.py), [`test_reminders_api.py`](../backend/tests/test_reminders_api.py)                                                                                    | [Pruebas mediante repositorios en memoria y puertos](../backend/tests/)                         |

## Descripción del aspecto A-01

**Nombre:** Captura inteligente de información académica

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite al estudiante registrar información académica mediante mensajes en lenguaje natural enviados al bot de Telegram, evitando la necesidad de abrir la aplicación móvil y completar formularios manualmente.

**Resultado esperado:** El sistema interpreta el mensaje mediante Gemini, identifica la intención y transforma la información en datos estructurados. El backend valida la información y la almacena en PostgreSQL para que pueda ser consultada y gestionada posteriormente desde la aplicación Flutter.

**Estado de la implementación:** este incremento entrega un **corte vertical parcial** de A-01: registro y consulta de tareas académicas mediante HTTP (`POST /academic/tasks`, `GET /academic/tasks`), con un adaptador de persistencia en memoria. La interpretación mediante Gemini y el canal de Telegram, así como el adaptador de PostgreSQL, quedan como trabajo pendiente para entregas posteriores; el diseño hexagonal del módulo permite incorporarlos sustituyendo adaptadores sin modificar el dominio ni los casos de uso.

## Escenario de calidad relacionado

[S1 — Registro correcto de información académica](calidad/escenarios_calidad.md#escenario-1--registro-correcto-de-información-académica)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

**## Estado del corte vertical**

El corte vertical actual implementa el registro y consulta de tareas mediante la API HTTP del backend. El recorrido atraviesa el adaptador de API, los casos de uso de la aplicación, la entidad de dominio y el puerto de persistencia, utilizando `InMemoryTaskRepository` como adaptador de persistencia para el incremento actual.

Las integraciones con Telegram, Gemini y PostgreSQL forman parte de la arquitectura objetivo y serán incorporadas en incrementos posteriores.

---

## Descripción del aspecto A-02

**Nombre:** Usuarios y autenticación

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite identificar al estudiante que utiliza TAIA y proteger las operaciones que trabajan con información académica personal.

**Resultado esperado:** El estudiante puede registrarse, autenticarse y utilizar un token de acceso para ejecutar operaciones protegidas. El backend utiliza la identidad autenticada para asociar las operaciones y los datos al usuario correspondiente.

**Estado de la implementación:** A-02 se encuentra implementado mediante el módulo `usuario`. El backend proporciona registro, autenticación, consulta del usuario autenticado y mecanismos de autorización utilizados por los demás módulos. La identificación del usuario se utiliza como frontera para acceder a la información académica y a los recordatorios.

## Escenario de calidad relacionado

[S4 — Acceso únicamente a datos del propio estudiante](calidad/escenarios_calidad.md#s4--acceso-únicamente-a-datos-del-propio-estudiante)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

**## Estado de la implementación**

El módulo `usuario` implementa el registro y autenticación de estudiantes mediante una API HTTP protegida. La identidad obtenida de la autenticación se utiliza como contexto de las operaciones posteriores.

Las pruebas del módulo verifican el flujo de autenticación y el acceso mediante usuario autenticado.

---

## Descripción del aspecto A-03

**Nombre:** Asistente inteligente e interpretación de solicitudes

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite que el estudiante interactúe con TAIA mediante lenguaje natural sin tener que conocer directamente la estructura de los datos ni los endpoints del backend.

**Resultado esperado:** El mensaje del estudiante es recibido por el módulo de IA, interpretado mediante el proveedor LLM y transformado en una operación que puede ser ejecutada por los módulos correspondientes. La IA permanece separada de las reglas principales del dominio.

**Estado de la implementación:** A-03 cuenta con el módulo `ai`, una interfaz `LLM`, un adaptador para Gemini y un `AcademicGateway` que permite traducir operaciones de IA hacia los casos de uso académicos. La API `/ai/message` se encuentra implementada y protegida mediante autenticación. La ejecución con Gemini requiere la configuración de las credenciales del proveedor, por lo que el proveedor real se mantiene como integración configurable.

## Escenario de calidad relacionado

[S1 — Registro correcto de información académica](calidad/escenarios_calidad.md#escenario-1--registro-correcto-de-información-académica)

[S5 — Sustitución del modelo de IA](calidad/escenarios_calidad.md#s5--sustitución-del-modelo-de-ia)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

**## Estado de la implementación**

El módulo AI actúa como frontera entre la interacción conversacional y la lógica académica. La dependencia con el proveedor LLM se mantiene detrás de un puerto, mientras que `AcademicGatewayAdapter` permite que las operaciones interpretadas sean ejecutadas mediante los casos de uso de Academic.

La sustitución del proveedor de IA no requiere modificar directamente las entidades ni las reglas centrales del módulo académico.

---

## Descripción del aspecto A-04

**Nombre:** Recordatorios y notificaciones

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite asociar recordatorios a información académica y entregar una notificación al estudiante mediante un canal configurado.

**Resultado esperado:** El estudiante puede crear, consultar, modificar, completar y eliminar recordatorios asociados a tareas académicas. Cuando corresponde, el sistema puede enviar explícitamente la notificación mediante Telegram.

**Estado de la implementación:** A-04 se encuentra implementado mediante el módulo `reminders`. El módulo valida la existencia y pertenencia de la tarea académica asociada, administra el ciclo de vida del recordatorio y utiliza un puerto de notificación con un adaptador específico para Telegram.

## Escenario de calidad relacionado

[S2 — Entrega puntual de recordatorios](calidad/escenarios_calidad.md#s2--entrega-puntual-de-recordatorios)

[S3 — Respuesta del asistente ante un mensaje](calidad/escenarios_calidad.md#s3--respuesta-del-asistente-ante-un-mensaje)

[S4 — Acceso únicamente a datos del propio estudiante](calidad/escenarios_calidad.md#s4--acceso-únicamente-a-datos-del-propio-estudiante)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

**## Estado de la implementación**

El módulo `reminders` utiliza `InMemoryReminderRepository` como persistencia actual y un `NotificationSender` como puerto para desacoplar el envío de notificaciones.

El adaptador `TelegramNotificationSender` conecta el sistema con Telegram mediante la API externa. En el incremento actual el envío es explícito mediante `POST /reminders/{id}/notify`; la ejecución automática exactamente en `scheduled_at` queda como evolución posterior.

---

## Descripción del aspecto A-05

**Nombre:** Integración y aislamiento entre módulos

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite que los módulos de TAIA colaboren sin concentrar toda la lógica en un único componente ni permitir accesos que ignoren el contexto del estudiante.

**Resultado esperado:** Usuario, Academic, AI y Reminders mantienen responsabilidades separadas y colaboran mediante casos de uso, puertos, adaptadores y gateways. Las operaciones sobre información académica y recordatorios utilizan el identificador del estudiante autenticado.

**Estado de la implementación:** A-05 se encuentra implementado mediante la organización modular del backend. `main.py` registra los routers de `academic`, `usuario`, `ai` y `reminders`, mientras que las dependencias entre módulos se realizan mediante interfaces y adaptadores específicos.

## Escenario de calidad relacionado

[S4 — Acceso únicamente a datos del propio estudiante](calidad/escenarios_calidad.md#s4--acceso-únicamente-a-datos-del-propio-estudiante)

[S5 — Sustitución del modelo de IA](calidad/escenarios_calidad.md#s5--sustitución-del-modelo-de-ia)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

**## Estado de la implementación**

La arquitectura actual mantiene los módulos separados dentro de `backend/app/modules/`. Academic y Reminders reciben el contexto del usuario para las operaciones que acceden a información privada. AI utiliza un gateway hacia Academic en lugar de acceder directamente al repositorio.

La suite automatizada constituye la evidencia global de que los módulos pueden evolucionar manteniendo sus responsabilidades separadas.

---

## Descripción del aspecto A-06

**Nombre:** Persistencia y evolución de infraestructura

**Usuario:** Equipo de desarrollo

**Problema que resuelve:** Evita que los casos de uso y las reglas de dominio dependan directamente del mecanismo concreto utilizado para almacenar información.

**Resultado esperado:** Los módulos utilizan puertos de persistencia que pueden ser implementados mediante diferentes adaptadores. Esto permite utilizar almacenamiento en memoria durante el desarrollo y sustituirlo posteriormente por PostgreSQL sin modificar las reglas centrales del dominio.

**Estado de la implementación:** A-06 se encuentra implementado parcialmente mediante `TaskRepository` e `InMemoryTaskRepository` en Academic y `InMemoryReminderRepository` en Reminders. PostgreSQL forma parte de la arquitectura objetivo, pero todavía no constituye el adaptador de persistencia utilizado por el recorrido ejecutable actual.

## Escenario de calidad relacionado

[S3 — Respuesta del asistente ante un mensaje](calidad/escenarios_calidad.md#s3--respuesta-del-asistente-ante-un-mensaje)

[S5 — Sustitución del modelo de IA](calidad/escenarios_calidad.md#s5--sustitución-del-modelo-de-ia)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

**## Estado de la implementación**

La persistencia está aislada mediante puertos y adaptadores. En Academic, los casos de uso dependen de `TaskRepository` y utilizan actualmente `InMemoryTaskRepository`. En Reminders se utiliza `InMemoryReminderRepository`.

Esta estructura permite que PostgreSQL sea incorporado posteriormente como un nuevo adaptador sin modificar las reglas principales de los casos de uso ni del dominio.

