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

# Entrada 06

Fecha: 2026-09-06

Herramienta: ChatGPT (OpenAI)

Objetivo: Analizar los resultados del autocalificador de las semanas 1 a 4 y orientar las correcciones posteriores del proyecto.

### Solicitud realizada

Se solicitó apoyo para interpretar los resultados de las evaluaciones automáticas de las semanas 1, 2, 3 y 4, diferenciando los incumplimientos reales de los criterios marcados como "No verificado", y para identificar las correcciones necesarias en la documentación y en la implementación.

### Resultado generado

La IA ayudó a:

* Revisar los criterios y observaciones entregados por el autocalificador.
* Diferenciar los estados `Cumple`, `No cumple` y `No verificado`.
* Identificar que un criterio `No verificado` no constituye evidencia de incumplimiento, sino ausencia de evidencia suficiente para que el agente pudiera comprobarlo.
* Identificar la necesidad de completar la trazabilidad del ADR-0001.
* Identificar la necesidad de contar con evidencia automatizada de ejecución de las pruebas.
* Revisar la relación entre arc42, C4, ADR, aspectos, código y pruebas.
* Revisar las correcciones necesarias para que la documentación reflejara correctamente el estado implementado y no presentara como terminadas integraciones futuras.
* Revisar la configuración de CI y la ejecución de las pruebas.

### Aceptado

* Utilizar los resultados del autocalificador como retroalimentación para mejorar el proyecto.
* Mantener la distinción entre arquitectura objetivo y funcionalidades actualmente implementadas.
* Completar la trazabilidad del ADR-0001.
* Incorporar evidencia de ejecución automatizada de las pruebas mediante CI.
* Mantener la estructura del corte vertical existente y mejorar su evidencia en lugar de crear una implementación duplicada.
* Mantener los componentes futuros claramente identificados como pendientes.

### Rechazado o modificado

* No se interpretaron los criterios `No verificado` como incumplimientos automáticos.
* No se presentó como implementada la integración completa con Telegram, Gemini, PostgreSQL o Flutter cuando dichas integraciones todavía corresponden a la arquitectura objetivo.
* No se creó una segunda prueba equivalente al recorrido ya cubierto por `test_academic_register_task.py`.
* No se eliminaron las pruebas históricas de entregas anteriores.

### Verificación realizada

El equipo contrastó las recomendaciones con el repositorio y aplicó las correcciones que correspondían.

La suite de pruebas fue ejecutada posteriormente mediante el entorno de CI y se obtuvo un resultado de:

```text
9 passed
```

También se verificó que el pipeline de GitHub Actions quedara correctamente configurado para ejecutar las pruebas.

## Entrada 07

Fecha: 2026-09-06

Herramienta: ChatGPT (OpenAI)

Objetivo: Documentar y justificar las correcciones realizadas a partir de los resultados de evaluación de las semanas 1 a 4.

### Solicitud realizada

Se solicitó apoyo para elaborar y revisar un documento en Markdown con las correcciones realizadas al proyecto, tomando como referencia los resultados del autocalificador y diferenciando los incumplimientos reales de los criterios que habían quedado como "No verificado".

### Resultado generado

La IA ayudó a organizar el documento de correcciones por semana, relacionando:

* Los hallazgos reportados por el autocalificador.
* Las correcciones realizadas posteriormente en el repositorio.
* La evidencia disponible para cada corrección.
* La diferencia entre criterios `No cumple` y `No verificado`.
* La evolución del proyecto entre las semanas 1 y 4.

También se revisó que las correcciones de la Semana 4 no presentaran como incumplimientos aquellos criterios de arc42 que el autocalificador marcó como `No verificado` por no haber inspeccionado su contenido.

### Aceptado

* Mantener en el documento la evaluación original realizada por el autocalificador.
* Reconocer explícitamente los incumplimientos reales.
* Explicar las correcciones aplicadas posteriormente.
* Diferenciar `No cumple` de `No verificado`.
* Documentar la evolución progresiva del repositorio.
* Incluir como contexto que el equipo fue incorporado al autocalificador aproximadamente un día antes de la Semana 3, por lo que inicialmente no conocía con suficiente anticipación todas sus métricas y convenciones.

### Rechazado o modificado

* No se presentó un criterio `No verificado` como evidencia de que el proyecto estuviera incompleto.
* No se ocultaron los incumplimientos reales identificados en las evaluaciones.
* No se atribuyeron al autocalificador errores que correspondieran a correcciones reales del proyecto.
* Se evitó presentar como corregidas funcionalidades que todavía pertenecen a la arquitectura objetivo o a incrementos futuros.

### Verificación realizada

El documento de correcciones fue contrastado con los resultados de evaluación de las semanas 1, 2, 3 y 4 y con el estado posterior del repositorio.

Entre las correcciones verificadas se encuentran:

* Actualización y completitud de la trazabilidad del ADR-0001.
* Corrección de referencias entre arquitectura, aspectos, código y pruebas.
* Consolidación de la documentación arc42.
* Incorporación y corrección de la configuración de GitHub Actions.
* Corrección de la configuración de pytest para ejecución desde la raíz del proyecto.
* Ejecución exitosa de la suite automatizada, con `9 passed`.
* Mantenimiento de la distinción entre arquitectura objetivo y funcionalidades actualmente implementadas.

La configuración de SonarCloud quedó identificada como pendiente de autorización inicial por parte del propietario de la organización.