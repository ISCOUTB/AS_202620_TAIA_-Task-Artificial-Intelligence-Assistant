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

## Entrada 03

**Fecha:** 2026-08-23

**Herramienta:** ClaudeCode (Anthropic)

**Objetivo:** Ajustar el C4 de contexto a lo recomendado por el docente.

### Solicitud realizada

Se solicitó un cambio en el código utilizado para la creación del diagrama de contexto C4. Se cambió de Structurizr a Mermaid, de acuerdo con los ajustes correspondientes indicados por el docente.

### Resultado generado

Se creó satisfactoriamente un documento Markdown con el código Mermaid que describe el diagrama de contexto que anteriormente se había creado con Structurizr y posteriormente importado como PNG.

### Aceptado

* Uso de Mermaid como formato para expresar el diagrama de contexto C4.
* Conservación de los elementos principales del diagrama de contexto previamente definido.
* Uso de un archivo Markdown como fuente editable y versionable del diagrama.
* Inclusión del diagrama Mermaid dentro de la documentación del proyecto.

### Rechazado o modificado

* Se modificó la implementación anterior basada en Structurizr y se reemplazó por Mermaid.
* Se dejó de utilizar el PNG como única fuente del diagrama, manteniendo el código Mermaid como fuente editable.
* Se ajustó la representación del diagrama para alinearla con las recomendaciones realizadas por el docente.

### Verificación realizada

El equipo revisó el diagrama generado y confirmó que representa los elementos y relaciones definidos para el contexto de TAIA, incluyendo el estudiante, TAIA, Telegram y Gemini. También se verificó que el código Mermaid quedara almacenado en el repositorio como documentación versionable.




## Entrada 04

**Fecha:** 2026-08-29

**Herramienta:** Claude (Anthropic), vía claude.ai

**Objetivo:** Recibir apoyo en el proceso de redacción de la documentación del corte vertical ejecutable en el README y en el llenado de la fila del aspecto A-01 en aspectos.

### Solicitud realizada

Se pidió apoyo para avanzar en la redacción de la sección del README que documenta el corte vertical ejecutable (alcance, endpoints, ejemplo de uso) y en el llenado de la fila A-01 de la tabla de aspectos.

### Resultado generado

Como parte del proceso, la IA sirvió de apoyo para:

* Avanzar en la redacción de un borrador de la sección "Corte vertical: registro de tareas (A-01)" del README (descripción del alcance, tabla de endpoints y ejemplo de uso con curl).
* Proponer un borrador de contenido para las columnas Requisito, C4, ADR, Código y Pruebas de la fila A-01 en aspectos, dejando "Evidencia" como pendiente.
* Identificar algunos enlaces de esa fila que no apuntaban correctamente a archivos del repositorio.


# Entrada 05

**Fecha:** 2026-08-30

**Herramienta:** ChatGPT (OpenAI)

**Objetivo:** Revisar y actualizar la documentación y las pruebas correspondientes al corte vertical de la semana 4.

### Solicitud realizada

Se solicitó apoyo para revisar la coherencia entre la arquitectura documentada y la implementación actual del proyecto, incluyendo las secciones 5, 6, 9, 10 y 12 de arc42, el C4 nivel 2, la tabla de aspectos y las pruebas automatizadas del corte vertical A-01.

### Resultado generado

La IA ayudó a:

* Revisar la correspondencia entre el C4 nivel 2 y la estructura actual del backend.
* Complementar y corregir redaccion sección 5 de arc42, correspondiente a los bloques de construcción.
* Complementar y corregir redaccion sección 6 de arc42, correspondiente a la vista de ejecución.
* Actualizar la sección 9 de arc42 con la referencia al ADR-0001.
* Actualizar la sección 10 de arc42 con los cinco escenarios de calidad definidos para TAIA.
* Iniciar la sección 12 de arc42 con un glosario de términos propios del sistema.
* Revisar la trazabilidad del aspecto A-01 en `docs/aspectos.md`.
* Revisar el README para que la documentación de las pruebas corresponda con el estado actual del repositorio.

### Aceptado

* Mantener las pruebas existentes de las semanas anteriores.
* Utilizar `test_academic_register_task.py` como evidencia de las pruebas asociadas al corte vertical A-01.
* Mantener `test_entrega3.py` como evidencia correspondiente a la entrega anterior.
* Completar la trazabilidad de A-01 mediante Requisito → C4 → ADR → Código → Pruebas → Evidencia.
* Documentar en arc42 la arquitectura implementada actualmente sin presentar como implementadas las integraciones futuras con Telegram, Gemini, PostgreSQL y Flutter.

### Rechazado o modificado

* Se descartó crear una prueba adicional cuando se determinó que `test_academic_register_task.py` ya podía utilizarse como evidencia del recorrido implementado.
* No se eliminó `test_entrega3.py`, para conservar la evidencia histórica de la entrega anterior.
* Se modificó la documentación para diferenciar entre la arquitectura objetivo y el corte vertical actualmente implementado.
* Se evitó presentar como implementados componentes que todavía corresponden a incrementos posteriores.

### Verificación realizada

El equipo revisó el repositorio actualizado y contrastó la documentación arquitectónica con la estructura actual del backend. Se verificó que el corte vertical implementado corresponde al registro y consulta de tareas mediante la API y que las pruebas existentes se mantienen separadas entre dominio, caso de uso y pruebas de la entrega anterior.

Queda pendiente verificar mediante ejecución de `pytest` que todas las pruebas se encuentren en verde y utilizar dicha ejecución como evidencia de la entrega.