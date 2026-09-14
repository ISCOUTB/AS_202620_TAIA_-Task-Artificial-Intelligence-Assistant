# Auditoría de fronteras y violaciones — S6

## Alcance y método

La auditoría se realizó sobre el código vigente del backend. Se revisaron:

- estructura de `backend/app/modules/`;
- entidades y repositorios de cada contexto;
- imports cruzados entre módulos;
- acceso a repositorios internos de otros contextos;
- operaciones de escritura y propiedad de entidades;
- contratos y adaptadores existentes para integraciones entre contextos.

El objetivo es distinguir **violaciones de propiedad de datos** de **violaciones de frontera modular**. Consultar un dato propiedad de otro contexto no convierte al consumidor en dueño del dato.

## Resultado de propiedad de datos

No se identificó una violación de doble escritura de una misma entidad de dominio en el estado auditado. La propiedad se encuentra concentrada en Usuario, Academic, AI y Reminders según `propiedad_datos_s6.md`.

## Violaciones y no conformidades detectadas

| ID | No conformidad | Ubicación concreta | Impacto | Estado |
|---|---|---|---|---|
| **V-01** | Dependencia directa de módulos hacia el adaptador HTTP de Usuario para obtener la identidad autenticada. | `backend/app/modules/academic/adapters/inbound/api.py`, `backend/app/modules/ai/adapters/inbound/api.py`, `backend/app/modules/reminders/adapters/inbound/http_controller.py` | Los contextos conocían una implementación interna de Usuario en lugar de depender de un contrato de identidad. | **Corregida** |
| **V-02** | Reminders obtenía directamente el repositorio interno de Academic. | `backend/app/modules/reminders/adapters/inbound/http_controller.py` → `academic.adapters.outbound.repository_provider.get_task_repository` | Reminders atravesaba la frontera de Academic y quedaba acoplado a su mecanismo interno de persistencia. | **Corregida** |
| **V-03** | El adaptador de AI hacia Academic obtenía directamente el repositorio y la entidad de dominio de Academic. | `backend/app/modules/ai/adapters/outbound/academic_gateway.py` | AI dependía de detalles internos de persistencia y dominio del contexto proveedor. | **Corregida** |
| **V-04** | La composición de dependencias requería una revisión final después de V-01–V-03. | `backend/app/main.py` y análisis de imports cruzados | Las implementaciones concretas deben quedar en el composition root y los consumidores deben comunicarse mediante contratos. | **Corregida** |

No se clasifica como violación de propiedad de datos el hecho de que Reminders o AI consulten una tarea académica: **consultar un dato de otro contexto no equivale a ser su propietario**. La violación aparece cuando el consumidor accede directamente al repositorio interno en lugar de utilizar el contrato del contexto propietario.

## Plan de corrección

| Violación | Acción de corrección | Resultado esperado | Evidencia futura |
|---|---|---|---|
| **V-01** | Definir un contrato de identidad en la capa de aplicación de Usuario y hacer que Academic, AI y Reminders consuman ese contrato. Mantener la autenticación HTTP como responsabilidad del adaptador de entrada. | Los módulos consumidores dejan de importar `usuario.adapters.inbound.api`. | Regla de dependencias + pruebas de autenticación y aislamiento. |
| **V-02** | Mantener `AcademicTaskLookup` como puerto de Reminders, pero conectar su implementación con una operación/fachada pública de Academic en lugar de `get_task_repository()`. | Reminders solicita una consulta académica sin conocer el repositorio interno de Academic. | Pruebas de asociación Reminder–Task y análisis de imports. |
| **V-03** | Mantener `AcademicGateway` como contrato de AI y cambiar su adaptador para consumir una interfaz de aplicación de Academic, sin acceder directamente al repositorio. | AI conserva su ACL y queda desacoplado de la persistencia concreta de Academic. | Pruebas de `test_ai_academic_gateway.py` y regla de dependencias. |
| **V-04** | Revisar la composición de adaptadores y proveedores después de V-01 a V-03. | Cada contexto se comunica mediante contratos explícitos y conserva la propiedad de sus datos. | Auditoría S6 repetida y pruebas completas del backend. |

Estas correcciones no implican un cambio del estilo arquitectónico definido para TAIA ni la extracción de microservicios. La arquitectura continúa siendo un monolito modular con organización hexagonal selectiva.

El objetivo de estas acciones es ajustar la implementación actual para que respete mejor las fronteras y responsabilidades de los módulos que ya forman parte de la arquitectura. En particular, se busca evitar dependencias directas hacia repositorios o adaptadores internos de otros contextos y favorecer la comunicación mediante contratos explícitos.

Por tanto, las acciones V-01 a V-04 deben entenderse como refinamientos y correcciones de la arquitectura existente, no como una nueva decisión arquitectónica ni como un cambio de patrón.

## Resultado de la auditoría final

La revisión posterior a V-01, V-02 y V-03 no encontró imports desde `AI` o `Reminders` hacia `academic.adapters.outbound.repository_provider`, ni imports desde `AI` hacia `academic.domain.entities.task`. La suite completa del backend queda en **74 pruebas aprobadas**.

La composición de dependencias concretas queda concentrada en `backend/app/main.py`, mientras los consumidores utilizan contratos de aplicación.

## Criterio de cierre

Se considerará corregida una violación cuando el consumidor se comunique con el proveedor mediante un contrato explícito y no dependa de sus adaptadores HTTP, repositorios o modelos internos.

Estas correcciones mantienen a TAIA como **monolito modular**. S6 no exige extraer microservicios; el objetivo es fortalecer las fronteras del dominio y la propiedad de datos.
