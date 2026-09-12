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

# Entrada 08

Fecha: 2026-09-11

Herramienta: ChatGPT (OpenAI)

Objetivo: Actualizar la documentación para que refleje la línea base ejecutable posterior a la integración de Usuario, Academic, AI y Reminders.

### Solicitud realizada

Se solicitó revisar y actualizar la documentación arquitectónica, C4, aspectos, escenarios de calidad y README después de implementar autenticación, integración AI-Academic, CRUD de Reminders y notificaciones mediante Telegram.

### Resultado generado

La IA ayudó a: 

* Contrastar la documentación existente con la estructura actual de `backend/app/modules/`.
* Diferenciar la arquitectura objetivo de los componentes realmente ejecutables.
* Actualizar el C4 nivel 2 para representar los módulos actualmente implementados.
* Documentar los recorridos ejecutables de Academic, AI y Reminders en arc42.
* Actualizar los escenarios de calidad para distinguir capacidades implementadas de capacidades pendientes.
* Registrar la evidencia actual de pruebas automatizadas.

### Aceptado

* Mantener PostgreSQL y Flutter como arquitectura objetivo mientras no estén implementados en esta línea base.
* Mantener Gemini como adaptador preparado, sujeto a configuración del proveedor.
* Documentar el envío explícito de notificaciones Telegram sin presentarlo como scheduler automático.
* Mantener la evidencia de `74 passed` obtenida mediante la suite automatizada.

### Verificación realizada

Se ejecutó `python -m pytest -q` sobre la línea base actual y se obtuvo:

```text
74 passed in 3.10s
```

# Entrada 09

Fecha: 2026-09-12

Herramienta: Claude Code (Anthropic)

Objetivo: Verificar la vigencia de los 45 problemas reportados por SonarQube tras la recuperación de la rama y corregirlos de forma incremental.

### Solicitud realizada

Tras una pérdida accidental de commits en `main` y su posterior recuperación desde la rama `val`, SonarQube pasó a reportar únicamente 3 problemas frente a los 45 registrados en `lista_problemas.md`. Se solicitó verificar directamente sobre los archivos si los 45 problemas seguían presentes, para decidir si corregir 3 o 45, y posteriormente corregirlos por tipo.

### Resultado generado

La IA ayudó a:

* Contrastar `lista_problemas.md` contra el contenido real de los archivos, confirmando que los 45 problemas seguían presentes en las líneas indicadas.
* Verificar que `origin/main` conservaba los 124 archivos `.py` y que la recuperación desde `val` no había perdido código.
* Descartar como causas del conteo de 3 el filtro de "New Code", un análisis obsoleto, un cambio de Quality Profile y la presencia de código no parseable.
* Detectar marcadores de conflicto de merge sin resolver en `.gitignore`, provenientes del commit "git ignore updated".
* Corregir los problemas agrupados por tipo, en commits separados.

### Correcciones aplicadas

| Problema reportado | Cantidad | Tratamiento |
| --- | --- | --- |
| Using dependencies without locking resolved versions | 1 | Se añaden `requirements.lock.txt` y `requirements-dev.lock.txt` con todas las dependencias transitivas y sus hashes; el CI instala con `--require-hashes`. |
| Document this HTTPException in the "responses" parameter | 17 | Cada adaptador HTTP declara un modelo `ErrorResponse` y constantes de módulo que los decoradores exponen mediante `responses`. |
| Return a value of type "TaskView" instead of "DataclassInstance" | 1 | Se sustituye `dataclasses.replace()` por la construcción explícita de `TaskView`. |
| Remove this commented out code | 1 | Se elimina el import comentado de `ReminderModel`. |
| Refactor this exception test to have only one invocation | 4 | La construcción previa se mueve fuera del bloque `with pytest.raises`. |
| Remove this redundant "response_model" parameter | 14 | Se elimina el parámetro; FastAPI infiere el mismo esquema desde la anotación de retorno. |
| Add logic to this except clause or eliminate it | 1 | Se elimina el `try/except InvalidTaskError: raise`, equivalente a no tenerlo. |
| Remove this redundant Exception class | 3 | `InvalidEmailError`, `InvalidUserError` y `AuthenticatedUserNotFoundError` derivan de `ValueError`, ya capturado. |
| Use "Annotated" type hints for FastAPI dependency injection | 2 | Se introduce el alias `BearerCredentials`, siguiendo el patrón de `CurrentUserId`. |

Total corregido: 44 de 45.

### Aceptado

* Corregir los 45 problemas verificados en el código y no los 3 que reportaba la herramienta, al confirmarse que los defectos eran reales.
* Mantener `lista_problemas.md` como referencia del alcance real.
* Separar `pytest` en `requirements-dev.txt`, dejando `requirements.txt` solo con dependencias de ejecución.
* Documentar también códigos de error que el código lanza y SonarQube aún no había marcado: el 503 de `/reminders/{id}/notify` y el 401/403 de `/users/login`.
* Usar constantes de módulo en lugar de diccionarios en línea, para no repetir descripciones entre endpoints.

### Rechazado o modificado

* Se descartó introducir un paquete compartido para el modelo `ErrorResponse`, para no alterar los límites entre módulos documentados en arc42; cada adaptador HTTP queda autocontenido.
* Se descartó corregir únicamente los 3 problemas visibles en SonarQube.
* No se modificó `requirements.txt` como fuente editable: los archivos `.lock.txt` son derivados y se regeneran con el comando documentado en su cabecera.
* Se conservaron `httpx` y `uvicorn` como dependencias de ejecución, al confirmarse que `gemini_llm.py` y `run.bat` las utilizan.

### Verificación realizada

Cada grupo de correcciones se validó ejecutando la suite completa y, en los cambios que afectan a los adaptadores HTTP, contrastando el esquema OpenAPI generado para confirmar que los modelos de respuesta se siguen infiriendo correctamente y que los códigos de error quedan documentados.

```text
74 passed
```

Queda pendiente un problema, "Split this composite assertion into separate assertions" en `backend/tests/test_ai_handle_message.py`.

Queda igualmente sin explicación la discrepancia entre los 45 problemas verificados en el código y los 3 que reporta SonarQube. Se comprobó que el análisis se ejecuta sobre el árbol actual, por lo que la causa corresponde a la configuración del proyecto en SonarCloud y no al contenido del repositorio.
