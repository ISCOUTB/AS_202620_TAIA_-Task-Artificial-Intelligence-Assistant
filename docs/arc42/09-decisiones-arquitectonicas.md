# 9. Decisiones arquitectónicas

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

## 9.3. Decisiones aplicadas en la implementación actual

ADR-0001 se refleja en la separación entre dominio, aplicación y adaptadores en Academic y Reminders, y en los puertos del módulo AI para LLM y AcademicGateway. Esta separación permitió integrar Reminders y el asistente sin trasladar detalles de Telegram o Gemini al dominio.

## 9.4. ADR-0002 — Integración HTTP síncrona con contrato OpenAPI

La estrategia de integración de la API principal está documentada en [ADR-0002](../adr/0002-estrategia-integracion-api-sincrona.md). La decisión establece HTTP síncrono + JSON y OpenAPI 3.1 como contrato versionado.
