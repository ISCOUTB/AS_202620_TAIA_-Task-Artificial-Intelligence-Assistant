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

Queda pendiente el mecanismo que dispara los recordatorios en su hora (S2), que se documentará en su propio ADR.

## 9.3. Decisiones aplicadas en la implementación actual

ADR-0001 se refleja en la separación entre dominio, aplicación y adaptadores en Academic y Reminders, y en los puertos del módulo AI para LLM y AcademicGateway. Esta separación permitió integrar Reminders y el asistente sin trasladar detalles de Telegram o Gemini al dominio.

## 9.4. ADR-0002 — Integración HTTP síncrona con contrato OpenAPI

La estrategia de integración de la API principal está documentada en [ADR-0002](../adr/0002-estrategia-integracion-api-sincrona.md). La decisión establece HTTP síncrono + JSON y OpenAPI 3.1 como contrato versionado.

## 9.5. ADR-0003 — Plataforma de despliegue de la API

La API se despliega en una VM `VM.Standard.E5.Flex` de Oracle Cloud con Docker, con la imagen en GitHub Container Registry y despliegue automático desde `main`. Se descartó Render Free por la suspensión tras 15 minutos sin tráfico, que incumple S3 y RNF-08 en la primera petición. La VM no es Always Free y cuesta 39,42 USD/mes. Ver [ADR-0003](../adr/0003-plataforma-despliegue-api.md).

## 9.6. ADR-0004 — Plataforma de la base de datos

La base de datos es Supabase PostgreSQL en el plan Free. Se descartaron PostgreSQL dentro de la VM (los datos quedarían atados a una sola VM, sin copias de seguridad) y Render Postgres Free (expira a los 30 días). Ver [ADR-0004](../adr/0004-plataforma-base-de-datos.md).

## 9.7. ADR-0005 — Normalización de la confirmación escrita en español

La confirmación de una escritura llega como texto libre del estudiante y se compara contra conjuntos cerrados. Se normalizan acentos, mayúsculas y signos antes de comparar, de modo que `Sí`, `SÍ`, `sí.` y `¡Sí!` equivalen a `si`. Se descartó enumerar variantes a mano y se descartó pedir al modelo de lenguaje que clasifique la respuesta, porque la confirmación es la última barrera antes de escribir y no debe depender de un componente no determinista. Ver [ADR-0005](../adr/0005-normalizacion-confirmacion-espanol.md).

## 9.8. ADR-0006 — Contratos de consulta y composición de casos de uso

Aceptado por el equipo. Academic traduce los
filtros de su contrato público y los controladores reciben casos de uso
compuestos en `main.py`. Ver [ADR-0006](../adr/0006-fronteras-y-evaluacion-verificable.md).

## 9.9. ADR-0007 — Comportamiento ante fallo o degradación del proveedor de lenguaje

Aceptado por el equipo. Ante un fallo de Gemini (red, timeout, `429`, `404`, `5xx` o respuesta malformada), el adaptador lo traduce a `LLMError` y el asistente responde un mensaje fijo de reintento, sin reintentar y sin escribir nada. Se descartaron los reintentos, porque consumen la misma cuota que provoca el fallo más frecuente; un proveedor de respaldo, porque exige otro adaptador y otra evaluación; un intérprete por reglas, por S1; y un `503`, porque el contrato de `/ai/message` no lo declara. Ver [ADR-0007](../adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md).
