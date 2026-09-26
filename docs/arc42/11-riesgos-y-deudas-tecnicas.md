# 11. Riesgos y deudas técnicas

Los siguientes riesgos y deudas técnicas se identifican a partir del estado actual de la línea base ejecutable.

## 11.1. Integraciones externas y funcionalidades pendientes

**Riesgo:** PostgreSQL y la ejecución completa de Gemini todavía no están habilitados en la línea base. Telegram sí dispone de vinculación y envío explícito de notificaciones.

**Impacto:** La solución ejecutable actual no demuestra todavía persistencia definitiva ni el recorrido completo con un proveedor LLM configurado.

**Mitigación:** Mantener las integraciones detrás de adaptadores y sustituir los repositorios en memoria por implementaciones persistentes cuando corresponda.

**Estado:** Parcialmente atendido.

## 11.2. Persistencia temporal en memoria

**Deuda técnica:** `InMemoryTaskRepository` se utiliza actualmente en lugar de PostgreSQL.

**Impacto:** Los datos no tienen persistencia permanente y no se pueden validar todavía aspectos propios de una base de datos real, como concurrencia, conexiones y persistencia entre ejecuciones.

**Mitigación:** Implementar un adaptador PostgreSQL que cumpla el contrato de `TaskRepository`, evitando modificar los casos de uso y las reglas del dominio.

**Estado:** Aceptada temporalmente para el corte vertical A-01.

## 11.3. Proveedor de IA pendiente de aislamiento completo

**Riesgo:** El adaptador Gemini existe, pero el recorrido real depende de configurar la credencial del proveedor.

**Impacto:** Todavía no se ha validado en código la sustitución de un proveedor de IA sin modificar la lógica de negocio.

**Mitigación:** Mantener el puerto `LLM` y encapsular la API del proveedor en `GeminiLLM`; habilitar la credencial en el entorno y validar el recorrido real.

**Relación:** S5 — Sustitución del modelo de IA.

**Estado:** Preparado; pendiente de validación con credenciales reales.

## 11.4. Disponibilidad de infraestructura gratuita

**Riesgo:** La infraestructura gratuita prevista puede suspender servicios por inactividad y presentar límites de uso.

**Impacto:** Las funcionalidades que dependan de ejecución programada, especialmente los recordatorios, podrían no ejecutarse exactamente en el horario esperado.

**Mitigación:** Diseñar el mecanismo de notificaciones teniendo en cuenta las restricciones del entorno gratuito y evaluar posteriormente una estrategia de ejecución programada más adecuada.

**Relación:** S2 — Entrega puntual de recordatorios.

**Estado:** Riesgo abierto.

## 11.5. Aislamiento de información entre estudiantes

**Riesgo:** Al incorporar persistencia real y el contexto del LLM, debe mantenerse el aislamiento entre estudiantes.

**Impacto:** Exposición de información académica y fallo del requisito de seguridad.

**Mitigación:** Mantener el control de acceso en el backend, asociar cada operación con el estudiante autenticado y validar la autorización antes de acceder a la persistencia. Las pruebas actuales cubren Academic y Reminders.

**Relación:** S4 — Acceso únicamente a datos del propio estudiante.

**Estado:** Implementado en los módulos actuales; pendiente de validación del contexto LLM real.

## 11.6. Cuotas y límites del proveedor LLM

**Riesgo:** El uso de Gemini bajo restricciones gratuitas puede limitar la cantidad de solicitudes y tokens disponibles.

**Impacto:** Solicitudes con demasiado contexto pueden superar las cuotas disponibles o aumentar el tiempo de respuesta.

**Mitigación:** Limitar y controlar el contexto enviado al modelo, estructurar las solicitudes y mantener el proveedor aislado para permitir su sustitución.

**Relación:** S1 — Registro correcto de información académica; S3 — Respuesta del asistente ante un mensaje; S5 — Sustitución del modelo de IA.

**Estado:** Riesgo abierto.

## 11.7. Evolución del monolito modular

**Deuda técnica:** El sistema se mantiene como un único despliegue.

**Impacto:** Si aumenta significativamente la complejidad o la carga, los módulos podrían requerir un mayor aislamiento.

**Mitigación:** Mantener límites claros entre módulos y dependencias mediante interfaces. Si el crecimiento futuro lo justifica, los módulos podrán evolucionar hacia componentes desplegables de forma independiente.

**Estado:** Decisión aceptada para el MVP.
