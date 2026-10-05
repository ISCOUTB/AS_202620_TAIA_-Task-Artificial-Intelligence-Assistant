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

# Entrada 10

Fecha: 2026-09-15

Herramienta: ChatGPT (OpenAI)

Objetivo: Implementar y documentar la evidencia de la Semana 7 sobre contrato de API, generación de cliente y prueba de contrato.

### Solicitud realizada

Se solicitó apoyo para definir una estrategia de integración HTTP síncrona con JSON, documentarla mediante OpenAPI 3.1, generar un cliente a partir del contrato y añadir una prueba que detectara cambios incompatibles.

### Resultado generado

La IA ayudó a estructurar:

* `docs/api/openapi.json` como contrato versionado.
* `backend/tests/test_api_contract.py` para comparar contrato e implementación.
* `backend/generated/taia_api_client.py` y `tools/generate_api_client.py` para generación determinista del cliente.
* `docs/adr/0002-estrategia-integracion-api-sincrona.md` para justificar HTTP síncrono + JSON + OpenAPI 3.1.
* Actualizaciones de arc42 §6 y C4-C2 para documentar los flujos y protocolos.

### Aceptado

* Mantener HTTP síncrono y JSON como estrategia de integración de la API principal.
* Usar OpenAPI 3.1 como contrato ejecutable y versionado.
* Ejecutar la prueba de contrato en GitHub Actions.
* Verificar en CI que el cliente generado permanezca sincronizado con el contrato.
* Mantener una demostración separada de cambio incompatible para no romper la rama principal.

### Rechazado o modificado

* No se incorporó Schemathesis como dependencia adicional, porque la prueba de contrato implementada ya compara directamente el contrato OpenAPI con el esquema generado por FastAPI y permite reproducir explícitamente un cambio incompatible.
* No se introdujo mensajería asíncrona para la API principal, porque el ADR-0002 documenta HTTP síncrono como decisión para S7.
* La evidencia de CI no se inventó en el repositorio: la URL y el resultado del run deben obtenerse de una ejecución real de GitHub Actions después del push.

### Verificación realizada

La suite local de contrato se ejecuta con `python -m pytest backend/tests/test_api_contract.py -q`. La demostración `tools/demo_contract_break.py` produce `AssertionError` y código de salida 1 al eliminar `/health` de la implementación. El workflow contiene pasos separados para ejecutar la prueba de contrato, regenerar el cliente y verificar su sincronización.

## Entrada 011

**Fecha:** 2026-10-03

**Herramienta:** Claude Code (Anthropic), con apertura de código del repositorio y ejecución de comandos en el entorno local del estudiante.

**Objetivo:** Implementar la entrega de la Semana 8 sobre una porción real del producto: la confirmación de escrituras por lenguaje natural en español (aspectos A-01 y A-03), con un defecto reproducible, una prueba que lo detecte y una corrección verificable.

### Solicitud realizada

Se pidió apoyo para: leer `backend/app/modules/ai/application/use_cases/handle_message.py`, localizar un defecto real en el manejo de la confirmación, escribir la prueba que lo expone antes de corregirlo, aplicar la corrección mínima y medir el resultado. Se pidió explícitamente que la línea base se repitiera sobre la rama `Mark` y no sobre la rama `migrate_to_dockploy` usada en un análisis previo.

### Resultado generado

La IA leyó el caso de uso y señaló el defecto en dos puntos conectados:

* `_YES` (línea 34) solo contenía `si` sin tilde, pese a que el producto atiende estudiantes hispanohablantes.
* `_resolve_pending` (línea 173) normalizaba únicamente con `.lower().strip(" .!?")`, de modo que `Sí` quedaba como `sí` y no coincidía con el conjunto.

También propuso y ejecutó, en el mismo trabajo, cuatro correcciones de entorno que no estaban en el encargo original pero que bloqueaban la medición:

* `backend/requirements.lock.txt` declaraba `python-dotenv` sin versión ni hash, por lo que `--require-hashes` no podía funcionar.
* Ambos lock files se generaron en Linux y omitían las dependencias exclusivas de Windows (`tzdata` vía `psycopg`, `colorama` vía `pytest`).
* `python-dotenv==1.1.1`, la versión fijada por el proyecto, está afectada por **CVE-2026-28684** (PYSEC-2026-2270): `set_key()` y `unset_key()` siguen enlaces simbólicos y permiten sobrescribir archivos arbitrarios.
* `backend/tests/test_usuario_auth_me.py` seguía vaciando `SqlAlchemyUserRepository._users`, un atributo en memoria que ya no existe.

### Aceptado

* **Opción A** para la normalización: eliminar tildes con `unicodedata`, pasar a minúsculas con `casefold()` y quitar signos de puntuación en los extremos. Se descartó añadir cada variante acentuada a mano a `_YES`.
* La corrección se limitó a una función auxiliar `_normalizar_respuesta`, sin tocar el flujo de confirmación ni los contratos del dominio.
* La prueba se escribió antes del arreglo, con 16 casos parametrizados: diez que deben crear la tarea y seis que no.
* La elevación de `python-dotenv` a `1.2.4`, versión que corrige la CVE. El código solo invoca `load_dotenv()`, cuyo comportamiento se verificó idéntico antes y después.

### Rechazado o modificado

* **Se rechazó usar la credencial de producción de Supabase que el estudiante proporcionó** para las pruebas de integración. `backend/tests/conftest.py` ejecuta `alembic downgrade base` al iniciar la sesión y `TRUNCATE` sobre las tablas de datos: apuntar `TEST_DATABASE_URL` a esa base habría destruido los datos de producción. Se sustituyó por un cluster PostgreSQL local desechable, con autenticación `trust` y puerto propio.
* **Se rechazó regenerar los lock files con la herramienta original en Linux**, porque eso habría vuelto a omitir las dependencias de Windows, que es precisamente el defecto que se quería cerrar. Las entradas se añadieron a mano con marcador `sys_platform == "win32"` y hash verificado contra PyPI.
* **Se modificó el alcance de CI**: hasta ese momento `.github/workflows/ci.yml` no definía `TEST_DATABASE_URL`, por lo que `conftest.py` omitía en silencio toda prueba de integración y el job pasaba sin ejercitar la capa de datos. Se añadió la variable, la creación de `taia_test` y la ejecución de la suite completa.
* **Se rechazaron las mediciones S1 (exactitud) y S3 (latencia p95) con Gemini.** No hay `GEMINI_API_KEY` en el entorno. Se construyó el arnés y el conjunto de evaluación, y ambos valores quedan marcados como pendientes en lugar de estimarse.

### Verificación realizada

* Línea base sobre la rama `Mark` antes de cualquier cambio de D-S8-01: `171 passed`, tras corregir los tres errores de `test_usuario_auth_me.py`. Evidencia en `docs/evidencia_s8_baseline.txt`.
* Con el defecto presente: `7 failed, 180 passed` en la suite completa, y los siete fallos son exactamente las variantes acentuadas; en el archivo aislado son `7 failed, 9 passed`. Evidencia en `docs/evidencia_s8_pre-fix.txt`, commit `74a5126`.
* Tras la corrección: `16 passed` en el archivo nuevo y `187 passed` en la suite completa, sin regresiones. Evidencia en `docs/evidencia_s8_post-fix.txt`.
* Integración continua: el commit `74a5126` produce una corrida roja pública y el commit `9160c4b` del arreglo la deja verde. La URL de ambas corridas está en las evidencias. Ninguno de esos push activó despliegue, porque `cd.yml` solo se ejecuta para `workflow_run` sobre `main`.

## Entrada 012

**Fecha:** 2026-10-03

**Herramienta:** Claude Code (Anthropic), con apertura de código del repositorio y ejecución de comandos en el entorno local del estudiante.

**Objetivo:** Cerrar el bloque de verificación de dependencias y credenciales de la entrega S8, y auditar si las fronteras de contexto y la propiedad de datos que S6 declaró cerradas seguían cerradas.

### Solicitud realizada

Se pidió: (a) comprobar que cada dependencia declarada exista y sea la legítima, con las vulnerabilidades reales de cada versión fijada; (b) comprobar que ninguna credencial real estuviera versionada; (c) reauditar la erosión de contexto y la propiedad de datos, partiendo de la auditoría de S6.

### Resultado generado

La IA construyó dos verificadores sin red ni base de datos.

`tools/verificar_dependencias.py` comprueba que todo paquete de los dos lock files tenga versión fijada y al menos un hash SHA-256, que las dependencias exclusivas de Windows estén presentes y que el árbol versionado no contenga credenciales de producción. Reporta 24 paquetes de producción y 31 de desarrollo, ninguno sin fijar, y **0 hallazgos** de credenciales. El escáner compone sus propios literales por trozos y se excluye a sí mismo del barrido, porque un detector de secretos que coincide consigo mismo no sirve.

`docs/verificacion_dependencias_s8.md` registra cuatro defectos y cómo se cerraron:

* **D-DEP-01** `python-dotenv==1.1.1` tiene la **CVE-2026-28684** (PYSEC-2026-2270, GHSA-mf9w-mj56-hr94): `set_key()` y `unset_key()` siguen enlaces simbólicos y pueden sobrescribir archivos arbitrarios. La exposición real de TAIA es baja porque el proyecto solo usa `load_dotenv()`. Se subió a 1.2.4.
* **D-DEP-02** `backend/requirements.lock.txt` declaraba `python-dotenv` sin versión ni hash. Con `--require-hashes` eso es un error obligatorio: la instalación de producción no podía funcionar.
* **D-DEP-03** Los locks se generaron en Linux y omitían `tzdata` y `colorama`, que solo se instalan en Windows. Eso explicaba por qué el CI en `ubuntu-latest` estaba verde y la instalación local en Windows era imposible.
* **D-DEP-04** `backend/Dockerfile` copiaba `uv` desde `:latest`, una etiqueta mutable. Ahora se fija por etiqueta y por digest.

La auditoría de erosión encontró algo que S6 había dado por cerrado. `docs/auditoria_violaciones_s6.md:48` afirma que "no encontró imports desde `AI` hacia `academic.domain.entities.task`", pero `ai/adapters/outbound/academic_gateway.py:19` importa `TaskStatus`. La misma nota, en `arc42/08-conceptos-transversales.md:118`, repetía una afirmación sobre la concentración de la composición que solo era cierta para dos de los cuatro contextos.

De ahí salieron cinco hallazgos. **E-01** era el más grave: `get_ai_use_case()` llamaba a `GeminiLLM.from_env()` en cada petición, y `GeminiLLM.__init__` abre un `httpx.Client` que ningún código de la aplicación cierra. Una fuga de cliente por petición, y sin reutilización cada llamada al modelo pagaba un apretón de manos TCP y TLS completo, que es exactamente lo que S3 mide como p95. **E-03** construía el store y el gateway al importar el módulo, con dos vidas distintas para los colaboradores de un mismo caso de uso. **E-04** convertía la falta de `GEMINI_API_KEY` en un 503 por petición mientras `/health` respondía `ok`, de modo que un despliegue roto pasaba la comprobación de CD.

### Aceptado

* **Mover la composición de IA a `backend/app/main.py`**, siguiendo el patrón de `configure_identity_service` y `configure_academic_task_management` que ya usaban Usuario y Academic. Un único `GeminiLLM` por vida del proceso, cerrado con el evento `lifespan`.
* **Cambiar el modo de fallo**: que la falta de la clave detenga el arranque en lugar de servir un servicio inservible. Es preferible no levantar antes que responder 503 a todo.
* **Exponer `usageMetadata` para S5** como `LLMUsage` en el puerto, registrado por el adaptador y anotado en el log. No se devuelve en la respuesta porque el contrato HTTP está congelado.
* **Una línea base para el auditor de fronteras**, con las infracciones ya analizadas y aceptadas. Sin ella el primer resultado habría sido ruidoso; con ella, el comando sale con código cero mientras no aparezca algo nuevo.

### Rechazado o modificado

* **No se corrigió E-05** (el import de `TaskStatus` al dominio de Academic). `TaskQuery.status` está tipado `TaskStatus | None`, así que no basta con pasar el string equivalente: hay que cambiar el contrato público de Academic, con su propio ciclo rojo-verde. Queda abierto y documentado, con la solución recomendada: que el puerto de Academic exponga la traducción del texto libre al estado canónico, para que sea Academic quien posea el vocabulario.
* **No se movió la composición de Reminders ni la de `structure_api` de Academic** (E-02). Son veinte dependencias entre archivos y un riesgo real sobre las 187 pruebas. Quedan en la línea base como R1 y el auditor marcará la regresión si empeoran.
* **Se rechazó medir S1 y S3 con Gemini.** Sin `GEMINI_API_KEY`, `tools/eval_llm.py` imprime que la medición queda pendiente y sale con código 2, distinto del 1 de una corrida fallida. Un precio de tokens no se escribe en el código: cambia con frecuencia y una tabla desactualizada daría un costo falsamente preciso; se pasa por parámetro.

### Verificación realizada

* `python tools/verificar_dependencias.py` → 24 y 31 paquetes, 0 sin fijar, 0 credenciales, veredicto `ok`.
* `python tools/audit_boundaries.py` → 9 adaptadores de entrada analizados, salida 0. Las reglas R3 y R4 de IA estaban en la línea base antes del cambio y **desaparecieron** después: esa es la evidencia de que E-03 y E-04 se corrigieron.
* Hashes de `python-dotenv` 1.2.4 y 1.2.2 calculados sobre la distribución descargada y contrastados con la API de PyPI; digest de `uv` obtenido del manifiesto OCI.
* `git log --all -S` sobre el patrón del *pooler* de Supabase y sobre el prefijo de la clave de Gemini: sin coincidencias en todo el historial.
* Suite completa: **193 pruebas** en verde tras el refactor, 202 tras añadir el dataset.

## Entrada 013

**Fecha:** 2026-10-03

**Herramienta:** Claude Code (Anthropic), con apertura de código del repositorio y ejecución de comandos en el entorno local del estudiante.

**Objetivo:** Cerrar los riesgos de configuración que permitirían que el proyecto se despliegue o se pruebe con secretos de desarrollo, y dejar la trazabilidad de S8 completa.

### Solicitud realizada

Se pidió: eliminar los valores por defecto de credenciales en `run.bat`, hacer alcanzable la plantilla de configuración que tres documentos ya referenciaban, y completar el documento maestro de la entrega.

### Resultado generado

`run.bat` definía dos valores por defecto. `un secreto JWT de desarrollo` contradecía directamente RNF-02, cuya razón de ser es que no exista valor por defecto y que la API no arranque sin secreto, y era además un secreto de firma publicado en el repositorio. El otro era peor en silencio: `load_dotenv` no sobrescribe variables ya definidas, así que el `DATABASE_URL` de `run.bat` tenía prioridad sobre `backend/.env` y el archivo del desarrollador se ignoraba sin aviso.

`tools/audit_boundaries.py` encontró además que `.gitignore` ignoraba `.env.example`, de modo que el archivo al que apuntaban el README, `cd.yml` y `arc42/07` no existía y no podía crearse sin `-f`. La ignorar queda anulada y la plantilla se versiona: una plantilla sin secretos es precisamente lo que pertenece al repositorio.

### Aceptado

* **`run.bat` sin ninguna credencial.** Comprueba que exista `backend/.env`, comprueba que `GEMINI_API_KEY` tenga valor, aplica migraciones y levanta Uvicorn.
* **Documentar en `.env.example` las seis variables** que el backend lee, y advertir que `conftest.py` ejecuta `alembic downgrade base` y `TRUNCATE`, de modo que `TEST_DATABASE_URL` nunca debe apuntar a la base de desarrollo.

### Rechazado o modificado

* **Se descartó `findstr /B` para comprobar la clave.** Exige que la coincidencia empiece en la posición 0, y un `.env` guardado como UTF-8 con BOM —que es lo que produce `Set-Content -Encoding utf8` de PowerShell 5.1— empieza con `EF BB BF`. Con `/B` la comprobación rechazaba siempre, incluso con la clave puesta. Se usa `for /f` separando por `=`, que sí distingue el valor vacío, y el trade-off queda anotado en el propio script: sin `/B` también encuentra una línea comentada, y en ese caso la API falla al arrancar con su propio `RuntimeError`.
* **Se corrigieron enlaces rotos que no eran de S8.** `docs/aspectos.md` y `docs/adr/0001` apuntaban a `test_academic_register_task.py` y `test_usuario_api.py`, que ya no existen. Una comprobación sobre los 39 documentos de `docs/` más el README deja ahora **0 enlaces relativos rotos**.

### Verificación realizada

* `cmd /c run.bat` sin clave → mensaje accionable y código de salida 1, en lugar de arrancar con un secreto publicado.
* Prueba de la lógica de comprobación con cuatro casos: valor vacío, valor presente, valor con espacio inicial y clave ausente.
* `python tools/eval_llm.py --dry-run` → 39 casos, cinco intenciones, mínimo tres por intención.
* Sin `GEMINI_API_KEY`, `tools/eval_llm.py` sale con código 2 y declara la medición pendiente.
* Integración continua verde en `eadc8f2` y `4eaa75c`, y en la cabeza actual `fa8fe6e`; 202 pruebas en verde en local.

## Entrada 014

**Fecha:** 2026-10-04

**Herramienta:** Claude (Anthropic), en conversación web. A diferencia de las entradas 011 a 013, **no tuvo acceso en vivo al repositorio**: analizó una copia extraída de `TAIA-nuevo.rar` en un entorno aislado. Los comandos sobre el equipo del estudiante los ejecutó el estudiante, y los resultados los interpretó la IA desde el texto pegado en la conversación.

**Objetivo:** Verificar la entrega S8 frente a la cadena pedida —aspecto, ADR, código, prueba que falla, medición, extracto de IA, auditoría de erosión, dependencias, credenciales y componente generativo— y cerrar la evaluación del componente generativo: exactitud, latencia y costo por operación.

### Solicitud realizada

Se pidió, en este orden: valorar qué tan avanzada y bien hecha estaba la entrega; corregir la configuración de credenciales (`.env` y `.env.example`); obtener una clave de Gemini; ejecutar `tools/eval_llm.py`; e interpretar y documentar los resultados.

### Resultado generado

La IA reprodujo la verificación sobre la copia del proyecto y entregó un informe con hallazgos, guías de comandos para PowerShell y un guion de diagnóstico (`tools/diag_fallos.py`) que repite los casos fallidos de uno en uno, con pausa, e imprime el **mensaje** completo del error en lugar de solo su tipo.

Hallazgos de la revisión:

- El `.env` de la raíz contenía una `DATABASE_URL` del *pooler* de Supabase con contraseña. No estaba versionado, pero viajaba dentro del archivo comprimido, y `tools/verificar_dependencias.py` no lo detecta porque solo escanea el árbol versionado.
- `gemini-2.5-flash`, el modelo por defecto del adaptador, devolvía **404** con una clave nueva.
- La primera corrida de `tools/eval_llm.py` dio **64,1 %** (25 de 39) con 10 errores `LLMError`. La IA los exportó como ruido y sin explicar; el estudiante los examinó.
- Faltaba la evaluación del componente generativo: había dataset y arnés, pero ningún resultado ni estimación de costo por operación.

### Aceptado

* **Cambiar el modelo a `gemini-3.5-flash-lite`.** Primero con la variable `GEMINI_MODEL`, sin tocar el adaptador, y después en el propio código: `_DEFAULT_MODEL` pasó de `gemini-2.5-flash` a `gemini-3.5-flash-lite` en `backend/app/modules/ai/adapters/outbound/gemini_llm.py`. Sin ese cambio, un clon sin `GEMINI_MODEL` recibiría 404. Se consultó la página oficial de deprecaciones de Google, que atribuye la restricción de los modelos 2.5 a las cuentas que ya los usaban, y la corrida que cierra la entrega confirmó que `gemini-3.5-flash-lite` responde: 39 llamadas, ninguna rechazada.
* **Pausar entre llamadas** en `eval_llm.py` (`PAUSA_ENTRE_LLAMADAS = 6`), porque el nivel gratuito de Gemini tiene límite de llamadas por minuto.
* **Guardar el mensaje del error**, no solo `type(error).__name__`, para que un fallo sea diagnosticable.
* **Declarar los precios por parámetro** y citar la fuente y la fecha: 0,30 USD de entrada y 2,50 USD de salida por millón de tokens, de la tabla de `gemini-3.5-flash-lite` en la documentación de Google, consultada el 2026-10-04.
* **Mover la clave de Gemini a `backend/.env`** y dejar `.env.example` sin valores reales. Verificado: `backend/.env` contiene la clave y `.env.example` la tiene vacía.
* **Eliminar el `.env` de la raíz** y **rotar la contraseña de Supabase**. Ambas hechas; ver la sección de verificación.

### Rechazado o modificado

* **Se rechazó el 64,1 % como medición válida.** Los diez errores no eran ruido aleatorio: nueve eran **consecutivos** en el orden del dataset (`u001` a `h004`), lo que un problema del modelo no explica. El diagnóstico con pausa de 6 segundos entre llamadas respondió **7 de 7 correctamente** en esos mismos casos (`u001`, `u003`, `u005`, `h001`, `h003`, `h004`, `x003`), lo que apunta al ritmo de las llamadas y no al modelo. La causa exacta —límite por minuto o saturación del servicio— **no se confirmó**, y no se afirma: el arnés solo guardaba el nombre del error, que era justamente lo que faltaba.
* **Se corrigió un dato de la propia IA.** Afirmó que las claves de Gemini empiezan por `AIza`; la clave del estudiante empezaba por otro prefijo. No se validó el formato por reglas, sino con una llamada real.
* **Se corrigió el diagnóstico del primer fallo.** El error `Illegal header value` no era ni la clave ni la red: `backend/.env` tenía un **espacio inicial** antes del valor, y `httpx` rechaza eso como cabecera. Se resolvió quitando el espacio del archivo, **no** en el código: `gemini_llm.py:100` sigue haciendo `os.getenv("GEMINI_API_KEY", "")` sin `.strip()`, así que un `.env` reescrito con `Set-Content` de PowerShell puede reproducirlo. Queda como deuda técnica.
* **Se aclararon los precios.** Primero se usaron 0,30 y 2,50 USD, que eran los de `gemini-2.5-flash`. Al cambiar de modelo, la IA los marcó como no válidos mientras no se contrastaran con la fuente. La tabla de `gemini-3.5-flash-lite` aportada por el estudiante los confirmó iguales, pero por el camino quedó escrito de dónde salían y de cuándo se habían consultado: es lo que hace comparables dos corridas de modelos distintos.
* **Se descartó escribir un segundo adaptador de otro proveedor.** Cerraría S5, pero es trabajo de código y pruebas fuera del alcance de esta entrega.
* **Se descartó `diag_fallos.py` como entregable.** Es una herramienta temporal de diagnóstico y no se versiona; la evidencia de que se ejecutó queda en esta entrada.
* **La clave de Gemini quedó expuesta en la conversación**, en un mensaje y en un *traceback*. Se eliminó en AI Studio y se creó otra.

### Verificación realizada

* **Credenciales, sobre el repositorio del estudiante.** `git log --all -S` sobre `.env` y `backend/.env`, y sobre el patrón del *pooler* de Supabase y el prefijo de la clave de Gemini: **sin coincidencias**. `git grep` sobre el árbol versionado, buscando clave de Gemini, URL con contraseña, clave PEM, token de GitHub y JWT: **0 hallazgos**. El `.env` de la raíz ya no existe.
* **Rotación de credenciales.** La contraseña de producción de Supabase **fue rotada** por el estudiante en el panel del proveedor. La clave de Gemini expuesta **fue eliminada en AI Studio** y la que está en uso es distinta.
* **Diagnóstico con pausa:** 7 de 7 casos que antes fallaban respondieron correctamente, en 1 068 a 1 882 ms.
* **Corrida válida, `docs/evaluacion_ia/resultado_s1_s3.json`:** 39 llamadas, **ningún error**, **32 de 39** (82,05 %) de acierto en intención; latencia p50 1 293,3 ms, p95 1 618,8 ms, máximo 1 687,5 ms sobre 39 muestras; 16 302 tokens de entrada y 2 915 de salida; 0,012178 USD, es decir **0,000312 USD por operación**. Tardó unos cuatro minutos con la pausa de seis segundos.
* **Llamada única de comprobación**, ejecutada por el estudiante: intención `create_task`, título `taller`, fecha 2026-10-09 (UTC-5), correcta para «el viernes» siendo domingo 2026-10-04.
* **Limitaciones que se declaran en `entrega_s8.md`:** S1 mide intención sobre 39 mensajes mientras el escenario habla de campos en 100; S3 mide el tramo del modelo desde el equipo del estudiante, no de extremo a extremo; y el arnés no aplica el descarte previo que el propio dataset declara para el caso vacío `x002`.
* **Pendiente:** el arnés no registra en el JSON qué modelo produjo el resultado. El modelo, la fecha y los precios están declarados en el documento maestro, no en el artefacto. Cerrarlo es trabajo futuro del arnés.
