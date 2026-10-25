# 8. Conceptos transversales

Esta sección documenta conceptos, reglas y convenciones que afectan a varios
módulos del sistema TAIA y que permiten mantener coherencia entre sus
fronteras, responsabilidades e integraciones.

Los detalles que requieren mayor extensión se mantienen en documentos
específicos dentro de `docs/` y se enlazan desde esta sección para evitar
duplicación.

## 8.1. Lenguaje ubicuo

El lenguaje ubicuo de TAIA se define a partir de los términos utilizados por los interesados y de los conceptos que aparecen en el código actual. El objetivo es que cada término tenga un significado estable dentro del contexto donde se utiliza y que los módulos no compartan modelos internos por conveniencia técnica.

| Término | Significado en TAIA | Contexto principal |
|---|---|---|
| **Estudiante** | Persona que utiliza TAIA para registrar y consultar información académica y recibir recordatorios. | Usuario |
| **Usuario** | Identidad autenticada que representa al estudiante dentro del sistema. | Usuario |
| **Tarea académica (Task)** | Información académica que representa una actividad que el estudiante debe realizar y que posee datos como título, descripción, asignatura, fecha y estado. | Academic |
| **Recordatorio (Reminder)** | Elemento programado asociado a una tarea académica para generar una comunicación al estudiante. | Reminders |
| **Notificación (Notification)** | Resultado o registro de un intento de comunicación asociado a un recordatorio. | Reminders |
| **Programación de recordatorio (ReminderSchedule)** | Información que representa la programación temporal de una notificación de recordatorio. | Reminders |
| **Conversación (Conversation)** | Representación de la interacción mantenida entre el estudiante y el asistente de IA. | AI |
| **Mensaje (Message)** | Unidad de comunicación procesada por el asistente dentro de una conversación. | AI |
| **Intención (Intent)** | Operación que el módulo de IA identifica a partir de un mensaje en lenguaje natural. | AI |
| **Confirmación** | Respuesta mediante la cual el estudiante acepta o rechaza una acción propuesta por el asistente. | AI |
| **Identidad Telegram** | Identificador externo utilizado para asociar un usuario de TAIA con una cuenta de Telegram. | Usuario |
| **LLM** | Modelo de lenguaje utilizado para interpretar mensajes y producir información estructurada. | AI |
| **Tarea académica consultable** | Representación mínima de una tarea que otro contexto necesita para realizar una operación, sin importar el modelo interno completo de `Task`. | Integración Academic |

### Reglas del lenguaje ubicuo

1. **Task** pertenece al contexto **Academic**. Otros contextos no deben tratar la entidad `Task` como propia.
2. **Reminder**, **Notification** y **ReminderSchedule** pertenecen al contexto **Reminders** y no son entidades de Academic.
3. **Conversation** y **Message** pertenecen al contexto **AI** y no representan datos académicos.
4. Los módulos que necesiten identificar al estudiante utilizan la identidad del usuario (`user_id`) y no deben manipular internamente la entidad `Usuario` como si fuera propia.
5. Una integración entre contextos debe utilizar un contrato explícito y traducir los conceptos necesarios, evitando compartir modelos internos por conveniencia.

## 8.2 Contextos delimitados

TAIA se organiza como un monolito modular compuesto por cuatro contextos
delimitados:

* **Usuario:** identidad, autenticación y datos propios del usuario.
* **Academic:** gestión de tareas académicas.
* **AI:** interpretación de solicitudes, conversaciones e intenciones.
* **Reminders:** gestión de recordatorios y notificaciones.

Cada contexto mantiene la responsabilidad de su propio modelo de dominio y
de los datos que modifica.

El detalle de responsabilidades, relaciones y datos de cada contexto se
encuentra en
[`docs/mapa_contextos_s6.md`](../mapa_contextos_s6.md).

## 8.3 Mapa de contextos y relaciones

Las relaciones entre contextos se establecen mediante contratos explícitos.
No se considera válido que un contexto acceda directamente a repositorios o
adaptadores internos de otro contexto.

No se identifica un **Shared Kernel** entre los contextos.

Las relaciones externas con Gemini y Telegram se aíslan mediante adaptadores
para evitar que los modelos de esos proveedores formen parte del dominio
interno de TAIA.

El mapa completo y la explicación de cada relación se mantienen en
[`docs/mapa_contextos_s6.md`](../mapa_contextos_s6.md).

## 8.4 Propiedad de datos

La regla transversal de propiedad de datos establece que cada entidad del
dominio tiene un único contexto responsable de modificarla.

| Contexto propietario | Datos bajo su responsabilidad                     |
| -------------------- | ------------------------------------------------- |
| **Usuario**          | `Usuario`, `TelegramLinkToken`                    |
| **Academic**         | `Task`                                            |
| **AI**               | `Conversation`, `Turn`, `Intent`, `PendingAction` |
| **Reminders**        | `Reminder`, `Notification`, `ReminderSchedule`    |

Los demás contextos pueden solicitar información mediante contratos, pero no
deben escribir directamente sobre los datos de otro contexto.

La auditoría actual no identifica una entidad con dos módulos propietarios.
El detalle de la correspondencia módulo → datos se encuentra en
[`docs/propiedad_datos_s6.md`](../propiedad_datos_s6.md).


## 8.5 Reglas de modularidad y comunicación entre contextos

Las fronteras de los contextos se mantienen mediante contratos explícitos.

Como regla arquitectónica:

1. Un módulo no debe depender directamente de los adaptadores inbound de otro
   módulo.
2. Un módulo no debe acceder directamente al repositorio interno de otro
   módulo.
3. Las interacciones entre contextos deben realizarse mediante puertos,
   interfaces o fachadas de aplicación.
4. Los adaptadores externos deben traducir los modelos externos al vocabulario
   propio del contexto que los consume.

Estas reglas buscan preservar la independencia de los contextos y facilitar
una eventual evolución o extracción de módulos.

## 8.6 Violaciones detectadas y plan de corrección

La auditoría S6 identificó cuatro situaciones de dependencia que fueron corregidas durante el refinamiento de las fronteras modulares.

| ID       | Situación corregida | Corrección aplicada | Estado |
| -------- | ------------------- | ------------------- | ------ |
| **V-01** | Academic, AI y Reminders dependían de funciones del adaptador HTTP de Usuario. | Se creó `IdentityService` en la capa de aplicación de Usuario y los consumidores dejaron de importar el adaptador HTTP. | **Corregida** |
| **V-02** | Reminders obtenía directamente el repositorio interno de Academic. | Se creó `AcademicTaskLookup` y su servicio de aplicación; Reminders consume ese contrato. | **Corregida** |
| **V-03** | AI obtenía directamente el repositorio interno y la entidad de dominio de Academic. | Se creó `AcademicTaskManagement` y su servicio de aplicación; `AcademicGatewayAdapter` consume DTOs del contrato. | **Corregida** |
| **V-04** | La composición de dependencias requería una revisión final. | `main.py` configura `IdentityService`, `AcademicTaskLookup`, `AcademicTaskManagement` y el caso de uso de IA. La comprobación es automática: `python tools/audit_boundaries.py`. Quedan abiertas E-02 (Reminders y `structure_api` aún componen en su adaptador HTTP) y E-05 (AI importa `TaskStatus` del dominio de Academic); ver [auditoria_erosion.md](../auditoria_erosion.md). | **Corregida** |

La suite automatizada del backend queda en **74 pruebas aprobadas** después de las correcciones.

La auditoría completa, con las rutas concretas del código y el plan de
corrección de cada caso, se encuentra en
[`docs/auditoria_violaciones_s6.md`](../auditoria_violaciones_s6.md).

Estas violaciones se consideran problemas de **dependencia entre contextos**,
no problemas de doble propiedad de datos.

## 8.7 Integraciones externas

TAIA integra servicios externos mediante adaptadores:

* **Gemini:** servicio utilizado para la interpretación mediante IA.
* **Telegram:** canal utilizado para enviar notificaciones.

Los modelos y contratos propios de estos proveedores no deben filtrarse hacia
el dominio interno de los contextos. Los adaptadores actúan como capa de
traducción entre el sistema externo y el modelo interno.

## 8.8 Relación con aspectos

Los contextos delimitados de esta sección se relacionan con los aspectos existentes del proyecto de la siguiente manera:

| Aspecto | Contextos relacionados | Justificación |
|---|---|---|
| **A-01 — Captura inteligente de información académica** | Academic, AI | La captura y registro de una tarea pertenece a Academic; AI interpreta la solicitud y traduce la intención hacia operaciones académicas. |
| **A-02 — Usuarios y autenticación** | Usuario | Usuario concentra identidad, autenticación y vinculación con Telegram. |
| **A-03 — Asistente inteligente e interpretación de solicitudes** | AI, Academic | AI gestiona conversación e interpretación; Academic mantiene las reglas y datos de las operaciones académicas. |
| **A-04 — Recordatorios y notificaciones** | Reminders, Academic, Usuario | Reminders es propietario de los recordatorios y notificaciones; Academic aporta la tarea asociada y Usuario aporta identidad/canal de comunicación. |
| **A-05 — Integración y aislamiento entre módulos** | Usuario, Academic, AI, Reminders | Este aspecto transversal depende directamente del respeto de los límites y de la ausencia de escrituras compartidas. |
| **A-06 — Persistencia y evolución de infraestructura** | Academic, Reminders | Cada contexto mantiene su puerto/adaptador de persistencia y conserva la propiedad de sus datos. |

La correspondencia anterior permite mantener la trazabilidad entre los aspectos de [docs/aspectos.md](../aspectos.md) y los contextos delimitados definidos en esta sección.

## 8.9 Coherencia con las vistas y decisiones arquitectónicas

Los contextos delimitados definidos en esta sección deben mantenerse
coherentes con:

* la vista de bloques de construcción de arc42;
* los diagramas C4;
* las decisiones arquitectónicas registradas en `docs/adr/`;
* los aspectos arquitectónicos registrados en `docs/aspectos.md`.

Si la definición de fronteras cambia respecto al corte arquitectónico
anterior, debe actualizarse la vista C4 correspondiente y registrarse la
decisión arquitectónica que explique el cambio.

El mapa de contextos y la propiedad de datos constituyen la referencia para
evaluar futuras modificaciones de la modularidad.

## 8.10 Consistencia de los datos

TAIA es un único proceso que escribe en una única base PostgreSQL
([ADR-0001](../adr/0001-estilo-arquitectonico.md),
[ADR-0004](../adr/0004-plataforma-base-de-datos.md),
[ADR-0009](../adr/0009-base-compartida-con-referencias-logicas-entre-modulos.md)).
Cada escritura es una transacción local de un solo módulo
(`session_factory.begin()` en su adaptador SQLAlchemy). No existe una
transacción que abarque dos módulos ni una llamada externa.

La garantía de cada operación se clasifica así:

* **Fuerte:** quien lee después de la escritura ve el resultado, y dos
  ejecuciones concurrentes no producen un estado imposible.
* **Eventual:** el estado correcto se alcanza, pero puede haber una ventana en
  la que se observa un estado intermedio o desactualizado.
* **Nombrada:** una garantía más débil que se acepta de forma explícita
  (al menos una vez, última escritura gana, sin atomicidad entre pasos).

### Operación → garantía

| Operación | Garantía | Mecanismo | Evidencia |
| --------- | -------- | --------- | --------- |
| Confirmar una acción pendiente del asistente (`RF-AGT-04`) | **Fuerte**, exactamente una vez el reclamo | `take_pending` lee y vacía la acción con `SELECT … FOR UPDATE` en una transacción corta; la segunda petición recibe `None`. | [`sqlalchemy_conversation_store.py:54-75`](../../backend/app/modules/ai/adapters/outbound/sqlalchemy_conversation_store.py), [`handle_message.py:96`](../../backend/app/modules/ai/application/use_cases/handle_message.py), prueba de ocho hilos en [`test_sql_persistence_replacements.py`](../../backend/tests/test_sql_persistence_replacements.py) |
| Reclamar la acción y crear la tarea en `academic` | **Nombrada: sin atomicidad entre pasos**, falla cerrado | El reclamo se confirma antes de escribir la tarea. Si la escritura falla, la acción se pierde y el estudiante repite el mensaje; nunca se crea dos veces. | [modos_fallo_s11.md, costo aceptado](../modos_fallo_s11.md#confirmación-de-una-acción-pendiente) |
| Crear la notificación de un recordatorio | **Fuerte**, idempotente | Bloqueo del recordatorio con `FOR UPDATE` y restricción `UNIQUE (reminder_id)`; si ya existe, se devuelve la existente. | [`sqlalchemy_reminder_repository.py:63-89`](../../backend/app/modules/reminders/adapters/outbound/sqlalchemy_reminder_repository.py), [diccionario_datos.md, §7.2](../diccionario_datos.md) |
| Enviar la notificación por Telegram | **Nombrada: al menos una vez** | `sendMessage` no admite clave de idempotencia. La lectura de `push_sent_at` antes de enviar está diseñada y pendiente. | [modos_fallo_s11.md, envío de una notificación](../modos_fallo_s11.md#envío-de-una-notificación) |
| Completar una tarea (`RF-TAR-07`) | **Fuerte**, idempotente | El dominio conserva el primer `completed_at`; repetir la operación no cambia el estado. | [`task.py:118-122`](../../backend/app/modules/academic/domain/entities/task.py) |
| Editar una tarea | **Nombrada: última escritura gana** | El caso de uso lee la tarea y la guarda con `session.merge` en sesiones distintas, sin versión. Dos ediciones simultáneas de la misma tarea conservan la última. Se acepta porque cada tarea pertenece a un solo estudiante. | [`manage_tasks.py:54-69`](../../backend/app/modules/academic/application/use_cases/manage_tasks.py), [`sqlalchemy_task_repository.py:23-25`](../../backend/app/modules/academic/adapters/outbound/sqlalchemy_task_repository.py) |
| Crear un recordatorio para una tarea | **Eventual** respecto a la tarea | `reminders` valida la tarea con `AcademicTaskLookup` y luego escribe en otra transacción. Si la tarea se elimina entre ambos pasos, el recordatorio apunta a una tarea borrada; el borrado es lógico (RT-04), así que no queda huérfano. | [`create_reminder.py:15-23`](../../backend/app/modules/reminders/application/use_cases/create_reminder.py), [diccionario_datos.md, §1](../diccionario_datos.md) |
| Consultar tareas, recordatorios e historial | **Fuerte** (lectura de lo confirmado) | Se lee directamente de PostgreSQL en cada petición, sin caché (ver §8.11). `status` y `priority` se calculan con la hora de la consulta. | [`sqlalchemy_task_repository.py:35-40`](../../backend/app/modules/academic/adapters/outbound/sqlalchemy_task_repository.py), [diccionario_datos.md, §9](../diccionario_datos.md) |

### Por qué no hace falta más

Las garantías nombradas se aceptan porque el daño es acotado: un recordatorio
duplicado molesta, pero no corrompe datos; una edición perdida solo puede
venir del mismo estudiante desde dos clientes. Si un módulo se extrajera a un
servicio, la fila «reclamar y crear la tarea» pasaría a ser una escritura por
red y necesitaría una clave de idempotencia o un outbox
([modos_fallo_s11.md, por qué no aplica una saga](../modos_fallo_s11.md#por-qué-no-aplica-una-saga),
[ADR-0008](../adr/0008-mantener-monolito-sin-extraer-modulos.md)).

## 8.11 Caché

### Decisión: no hay caché de lectura

TAIA **no guarda en caché datos de negocio**. Cada consulta llega a
PostgreSQL. El único `@lru_cache` del backend guarda el *engine* y la fábrica
de sesiones de SQLAlchemy
([`database.py:42-48`](../../backend/app/shared/adapters/outbound/database.py)):
son objetos de infraestructura creados una vez por proceso, no datos que se
puedan desactualizar.

| Pregunta | Respuesta para TAIA | Evidencia |
| -------- | ------------------- | --------- |
| ¿Hay carga que aliviar? | 0,2 peticiones por segundo en la hora pico y 5 KB leídos por petición. | [costo_mensual.md, §1](../costo_mensual.md) |
| ¿El objetivo de latencia está en riesgo? | RNF-08 exige p95 < 500 ms en CRUD. La latencia real por ruta se observa en `GET /metrics`; el costo dominante de S3 es el modelo, que no se puede cachear porque cada mensaje es distinto. | [`observability.py`](../../backend/app/shared/adapters/inbound/observability.py), [requerimientos.md](../requerimientos.md) |
| ¿Los datos se pueden reutilizar entre usuarios? | No. Todas las lecturas se filtran por `user_id`. | [arc42 §8.4](#84-propiedad-de-datos) |
| ¿Los datos son estables? | No. `status` (`overdue`) y `priority` dependen de la hora de la consulta; una respuesta guardada queda mal con solo pasar el tiempo. | [diccionario_datos.md, §9](../diccionario_datos.md) |

Una caché agregaría una fuente de datos desactualizados y una política de
invalidación que mantener, sin un problema medido que resuelva.

La expiración de `pending_action` (`pending_action_expires_at`) **no es una
caché**: es una regla funcional que define cuánto tiempo vale una propuesta
del asistente ([diccionario_datos.md, §8.1](../diccionario_datos.md)).

### Disparador y diseño si se introduce

La decisión se revisa si `GET /metrics` muestra el p95 de `GET /tasks` por
encima de 500 ms con la base sana. En ese caso el diseño acotado sería:

| Aspecto | Diseño |
| ------- | ------ |
| **Qué** | La lista de asignaturas del estudiante (`subjects.list_by_user`), que se consulta para resolver el nombre de la asignatura al listar tareas ([`task_management.py:99-100`](../../backend/app/modules/academic/application/services/task_management.py)) y cambia poco. **No** las tareas: su estado depende de la hora. |
| **Dónde** | En memoria del proceso de la API, con clave `user_id`. Si Dokploy ejecuta más de una réplica, cada una tendría su copia; por eso el TTL es corto y la invalidación es local. |
| **Cuánto** | TTL de 60 segundos y un máximo de 1 000 entradas (100 estudiantes activos con holgura). |

### Política de invalidación tras escritura

Si se introduce la caché anterior:

1. Crear, renombrar, archivar o eliminar una asignatura **borra la entrada de
   ese `user_id`** después de confirmar la transacción, en el mismo caso de uso
   (`manage_subjects.py`).
2. Crear, editar, completar, reabrir o eliminar una tarea **no toca la caché**,
   porque las tareas no se guardan en ella; la siguiente lectura las obtiene de
   PostgreSQL.
3. En otra réplica, la entrada vieja vence por TTL: se acepta hasta 60 segundos
   de un nombre de asignatura desactualizado, nunca una tarea desactualizada.
4. Si la escritura falla, no se invalida nada, porque la caché sigue
   coincidiendo con la base.