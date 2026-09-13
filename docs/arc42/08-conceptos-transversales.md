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

La auditoría del código actual identifica las siguientes situaciones que
deben corregirse para hacer cumplir completamente las fronteras definidas.:

| ID       | Violación                                                                                  | Corrección                                                                                                                               |
| -------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **V-01** | Academic, AI y Reminders dependen directamente de funciones del adaptador HTTP de Usuario. | Mover el contrato de identidad a una interfaz de aplicación y mantener la autenticación HTTP como responsabilidad del adaptador inbound. |
| **V-02** | Reminders obtiene directamente el repositorio interno de Academic.                         | Conectar `AcademicTaskLookup` con una interfaz/fachada de aplicación de Academic.                                                        |
| **V-03** | AI obtiene directamente el repositorio interno de Academic.                                | Mantener `AcademicGateway` como contrato y hacer que su implementación utilice la interfaz de aplicación de Academic.                    |
| **V-04** | La composición de dependencias debe revisarse después de corregir V-01–V-03.               | Verificar que las interacciones finales se produzcan exclusivamente mediante contratos explícitos.                                       |

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