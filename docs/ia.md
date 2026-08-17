# Registro de uso de IA

## Entrada 001

**Fecha:** 2026-08-06

**Herramienta:** ChatGPT (OpenAI)

**Objetivo:** Explorar alternativas para el proyecto integrador y definir una propuesta de arquitectura para un asistente universitario inteligente.

### Solicitud realizada

Se solicitó ayuda para definir la arquitectura del sistema y las tecnologías apropiadas (tecnologías 0 costo).

### Resultado generado

La IA propuso una arquitectura basada en:

* Flutter para la aplicación móvil.
* FastAPI para el backend.
* PostgreSQL para persistencia.
* Telegram Bot API para captura rápida.
* Gemini API para interpretación de lenguaje natural.

### Aceptado

* Enfoque del proyecto como asistente universitario.
* Uso de Telegram como canal de captura.
* Uso de PostgreSQL y FastAPI.
* Definición del aspecto A-01.

### Rechazado o modificado

* Se descartó construir una aplicación exclusivamente de finanzas.
* Se redujo el alcance del MVP para concentrarse primero en el registro de tareas.

### Verificación realizada

El equipo revisó la propuesta y confirmó que es construible con herramientas gratuitas, que puede desplegarse progresivamente y que el aspecto inicial permite un corte vertical funcional, coherente con los objetivos del curso.

## Entrada 002

**Fecha:** 2026-08-13

**Herramienta:** ChatGPT (OpenAI)

**Objetivo:** Refinar el planteamiento definitivo del proyecto.

### Solicitud realizada

Se solicitó apoyo para analizar y consolidar la nueva propuesta del proyecto como un asistente académico inteligente para estudiantes universitarios.

### Resultado generado

La IA ayudó a:

* Consolidar el proyecto como un asistente académico inteligente, dejando de lado el enfoque inicial de finanzas.
* Definir el alcance del MVP alrededor de la gestión de información académica.
* Mantener Telegram como canal de captura rápida y Flutter como aplicación principal.
* Definir Gemini como componente encargado de interpretar mensajes en lenguaje natural.
* Mantener FastAPI como backend y PostgreSQL como mecanismo de persistencia.
* Establecer que Gemini no tendrá acceso directo a PostgreSQL y que el backend será responsable de validar la información antes de almacenarla.
* Diferenciar las funcionalidades iniciales del MVP de las funcionalidades futuras, como RAG, embeddings, procesamiento de documentos y tutor académico personalizado.
* Actualizar el aspecto A-01 para enfocarlo en la captura inteligente de información académica.
* Orientar la documentación de la segunda entrega hacia arc42 (secciones 1–3), árbol de utilidad, escenarios de calidad, restricciones justificadas y C4 de contexto.

### Aceptado

* Enfoque definitivo como asistente académico inteligente.
* Uso de Telegram como canal de captura rápida.
* Uso de Flutter, FastAPI, PostgreSQL y Gemini.
* Separación entre la interpretación realizada por Gemini y la persistencia controlada por el backend.
* Definición del aspecto A-01 como "Captura inteligente de información académica".
* Separación entre el alcance del MVP y las funcionalidades futuras.
* Organización de la documentación de acuerdo con los entregables del proyecto.

### Rechazado o modificado

* Se descartó definitivamente el enfoque de aplicación de finanzas.
* Se modificó el aspecto A-01, que inicialmente estaba enfocado únicamente en el registro de tareas desde Telegram, para abarcar la captura inteligente de diferentes tipos de información académica.
* Se evitó incluir RAG, embeddings y base de datos vectorial dentro del MVP, dejándolos como funcionalidades futuras.
