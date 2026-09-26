# 1. Introducción y objetivos

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

## 1.1. Resumen de requisitos

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
ausencia no invalida el producto.

El primer corte vertical es el aspecto A-01, que implementa actualmente el
recorrido de registro de tareas mediante la API HTTP → caso de uso →
dominio → repositorio en memoria. La integración con Telegram, la
interpretación mediante el LLM, la persistencia en PostgreSQL y la
visualización en la aplicación forman parte de la arquitectura objetivo y
serán incorporadas en iteraciones posteriores.

## 1.2. Objetivos de calidad

Los objetivos de calidad de TAIA se priorizan de acuerdo con su impacto sobre la utilidad del sistema y el riesgo técnico asociado.

| Priority | Quality Goal | Description | Related Scenario |
|---|---|---|---|
| 1 | **Seguridad y privacidad** | Garantizar que cada estudiante pueda acceder únicamente a su propia información académica y que los intentos de acceso no autorizado sean rechazados. | S4 — Acceso únicamente a datos del propio estudiante |
| 2 | **Exactitud** | Garantizar que la información académica expresada en lenguaje natural sea interpretada y registrada correctamente. | S1 — Registro correcto de información académica |
| 3 | **Puntualidad** | Garantizar que los recordatorios académicos sean entregados cerca de la hora programada. | S2 — Entrega puntual de recordatorios |
| 4 | **Rendimiento** | Mantener tiempos de respuesta adecuados para las interacciones con el asistente. | S3 — Respuesta del asistente ante un mensaje |
| 5 | **Mantenibilidad** | Permitir la sustitución del proveedor o modelo de IA sin modificar la lógica de negocio principal ni la persistencia del sistema. | S5 — Sustitución del modelo de IA |

Los objetivos se consideran prioritarios porque TAIA gestiona información académica personal, depende de servicios externos para la interpretación mediante IA y requiere ofrecer una interacción suficientemente rápida y confiable para resultar útil al estudiante.

## 1.3. Interesados

| Rol | Quién | Expectativa |
|---|---|---|
| Estudiante usuario | Estudiantes de la universidad; a futuro, de otras universidades | Registrar tareas sin fricción, recibir recordatorios fiables y obtener un plan de estudio realista |
| Equipo de desarrollo | Luis Mendoza, Deiner Gonzales, Valeria Berrio, Mark Pastrana | Una arquitectura comprensible y documentada que puedan construir entre cuatro personas dentro del plazo del curso |
| Docente evaluador | Profesor del curso de Arquitectura de Software | Documentación arquitectónica trazable (requisito → C4 → ADR → código → pruebas → evidencia) y uso de IA registrado |
