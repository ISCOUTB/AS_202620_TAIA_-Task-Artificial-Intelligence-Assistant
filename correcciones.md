# Justificación de la calificación de las semanas 1 a 4

## 1. Objetivo del documento

Este documento consolida los hallazgos identificados durante las semanas 1 a 4 y registra las acciones realizadas posteriormente para corregirlos o contrastarlos con el estado actual de TAIA.

Para cada hallazgo se indica:

* origen de la observación;
* hallazgo identificado;
* acción realizada;
* justificación técnica;
* evidencia actual en el repositorio;
* estado de la corrección.

Los estados utilizados son:

* **Corregido:** la deficiencia histórica fue atendida y existe evidencia actual.
* **Parcial:** existe una corrección, pero permanece una condición pendiente.
* **Pendiente:** la deficiencia continúa abierta.
* **No verificado:** no existe evidencia suficiente para determinar el estado actual.

Esta clasificación permite distinguir entre una deficiencia histórica y una deficiencia que continúa presente en el estado actual del proyecto.

---

# 2. Semana 1

## 2.1 Tabla original de evaluación

| Criterio                                                                  | Evidencia técnica                                                                                                                        | Estado        | Observaciones                                                                                                                                                    |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repositorio creado en la organización con el nombre de la convención      | `revisiones/2026-2/_meta/lsremote.txt:18` (`AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant OK`); protocolo git sin autenticación | Cumple        | Visible y público |
| Integrantes del equipo con acceso                                         | `git shortlog -sne 76d4a91`: solo `val` (1 commit)                                                                                       | No verificado | Sin API no se listan colaboradores. Hasta el cierre solo consta una cuenta; `luis20072002` (15-ago), `dei0811` y `mark` (16-ago) aparecen en la semana siguiente |
| Equipo de 3 o 4 personas                                                  | `EQUIPOS.md:33`                                                                                                                          | Cumple        | 4 integrantes declarados                                                                                                                                         |
| Ficha del problema con usuarios y alcance                                 | `docs/ficha_problema.md` en `76d4a91`                                                                                                    | Cumple        | Usuarios objetivo y alcance del MVP declarados con claridad                                                                                                      |
| Dos tensiones de calidad declaradas y enfrentadas entre sí                | `git grep -niE 'tension                                                                                                                  | tensión       | calidad' 76d4a91 -- docs`: sin resultados                                                                                                                        |
| `docs/aspectos.md` con la tabla y un aspecto en sus dos primeras columnas | `docs/aspectos.md` en `76d4a91`                                                                                                          | Cumple        | Tabla de 8 columnas con ID `A-01` y requisito `RF-01`                                                                                                            |
| `docs/ia.md` iniciado con contenido real                                  | `docs/ia.md` en `76d4a91`                                                                                                                | Cumple        | Entrada 001 (06-ago) con herramienta, aceptado, rechazado y verificación                                                                                         |
| Plantilla arc42 descomprimida en `docs/arc42/`, en Markdown               | `docs/arc42/arc42-template-EN.md` en `76d4a91`                                                                                           | Cumple        | Un archivo Markdown con las 12 secciones                                                                                                                         |
| `docs/adr/` y `docs/c4/` creados                                          | `git ls-tree -r 76d4a91`: no existen `docs/adr/` ni `docs/c4/`                                                                           | No cumple     | Ninguno de los dos directorios creado al cierre de S1                                                                                                            |

### Matriz transversal

| Criterio                                                                 | Evidencia técnica                                                                                                                                 | Estado    | Observaciones                                               |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------- |
| Repositorio en la organización, con el nombre de la convención y público | `lsremote.txt:18`                                                                                                                                 | Cumple    | —                                                           |
| Estructura mínima presente                                               | `git ls-tree -r 76d4a91`: `README.md`, `docs/arc42/`, `docs/aspectos.md`, `docs/ia.md`, `docs/ficha_problema.md`; faltan `docs/adr/` y `docs/c4/` | No cumple | Estructura incompleta al cierre de S1                       |
| Estado calificado identificable                                          | `76d4a916972819159a2d981302c0be8b82ffde79` · `2026-08-07T03:34:26-05:00`                                                                          | Cumple    | Commit anterior al cierre, sin etiqueta                     |
| Nombres de ADR según la convención                                       | No existe `docs/adr/`                                                                                                                             | Cumple    | Sin ADR; filtro vacío                                       |
| ADR aceptados no reescritos                                              | Sin ADR                                                                                                                                           | Cumple    | No aplica por ausencia                                      |
| `docs/ia.md` al día para la semana                                       | commit `76d4a91` (07-ago) dentro del periodo; Entrada 001 con aceptado, rechazado y verificación                                                  | Cumple    | —                                                           |
| Sin credenciales en el repositorio ni en el historial                    | `git grep` regex §9 sobre `76d4a91`: sin coincidencias; sin `.env`; `git log -S'BEGIN PRIVATE KEY'`: vacío                                        | Cumple    | —                                                           |
| Contribución de todos los integrantes                                    | `git shortlog -sne 76d4a91`: 1 persona de 4                                                                                                       | No cumple | Solo `val` antes del cierre; los otros tres no aparecen aún |

**Resultado informado por el autocalificador: 6 de 9 criterios cumplidos.**

## 2.2 Justificación

### Resultados que consideramos correctos

Los siguientes aspectos estaban efectivamente cumplidos:

* El repositorio tenía el nombre y ubicación establecidos.
* El equipo estaba declarado con cuatro integrantes.
* La ficha del problema estaba creada.
* `docs/aspectos.md` y `docs/ia.md` ya estaban iniciados.
* La plantilla arc42 ya se encontraba incorporada.

Estos resultados están respaldados directamente por la evidencia de S1.

### Hallazgos originales

En S1 se identificaron, entre otros, los siguientes puntos:

* no estaban explicitadas dos tensiones de calidad;
* no existían todavía `docs/adr/` y `docs/c4/`;
* el historial visible mostraba inicialmente la participación de un solo integrante.

Estos hallazgos fueron aceptados como deficiencias correspondientes al estado de S1.

### Contraste con el estado actual

| Origen | Hallazgo                                                 | Acción realizada                                                          | Evidencia actual                         | Estado    |
| ------ | -------------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------- | --------- |
| S1     | No estaban explicitadas las tensiones de calidad         | Se consolidaron los escenarios y documentación de calidad                 | `docs/calidad/` y `docs/arc42/`          | Corregido |
| S1     | No existía `docs/adr/`                                   | Se incorporó ADR-0001                                                     | `docs/adr/0001-estilo-arquitectonico.md` | Corregido |
| S1     | No existía `docs/c4/`                                    | Se incorporaron las vistas C4                                             | `docs/c4/C4-C1.md`, `docs/c4/C4-C2.md`   | Corregido |
| S1     | Participación inicialmente visible de un solo integrante | El historial posterior incorpora contribuciones de los cuatro integrantes | Historial Git / `git shortlog -sne HEAD` | Corregido |

---

# 3. Semana 2

## 3.1 Tabla original de evaluación

| Criterio                                                      | Evidencia técnica                                      | Estado        | Observaciones                                                                                                                                                                                                                |
| ------------------------------------------------------------- | ------------------------------------------------------ | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| arc42 sección 1 con objetivos de negocio y su interesado      | `docs/arc42/arc42-template-EN.md:18-98` en `59590c9`   | Cumple        | Objetivos de calidad con motivación y métrica (76-88) y tabla de Stakeholders rellena con expectativas (91-96)                                                                                                               |
| arc42 sección 2 con restricciones clasificadas y justificadas | `docs/arc42/arc42-template-EN.md:99-134`               | No cumple     | Clasificadas en técnicas, organizacionales y convenciones, cada una con su implicación arquitectónica (excelente justificación), pero no hay categoría legal                                                                 |
| Restricciones separadas de los requisitos                     | sección 2 (99-134) vs «Requirements Overview» (42-74)  | Cumple        | Separación clara, incluida la distinción MVP / deseable / fuera de alcance                                                                                                                                                   |
| arc42 sección 3 con actores y sistemas externos               | `docs/arc42/arc42-template-EN.md:135-149`              | No cumple     | «Context and Scope» conserva los placeholders de plantilla (`\<Diagram or Table\>`); sin actores ni sistemas externos identificados                                                                                          |
| Entre 3 y 5 escenarios de calidad redactados                  | `docs/calidad/escenarios_calidad.md` en `59590c9`      | Cumple        | 5 escenarios redactados. Desviación de estructura: viven en `docs/calidad/`, no en la sección 10 del arc42, que quedó vacía (líneas 297-303)                                                                                 |
| Cada escenario con sus seis partes y medida numérica          | `docs/calidad/escenarios_calidad.md`                   | No cumple     | Los 5 desglosan las seis partes, pero el escenario 5 («Sustitución del modelo de IA») no tiene medida numérica («el cambio queda solo en la capa de adaptador» = enunciado). Los otros 4 sí tienen cifra, unidad y condición |
| Árbol de utilidad que prioriza por impacto y riesgo           | `docs/calidad/arbol_utilidad.md`                       | No cumple     | Es una jerarquía plana de atributos, sin valores de impacto ni riesgo                                                                                                                                                        |
| C4 de contexto con leyenda y flechas etiquetadas              | `docs/c4/C4-ContextoTAIA.png` (solo imagen, no código) | No verificado | El archivo existe (378 KB), pero este agente no puede inspeccionar imágenes: haría falta abrir el PNG para comprobar leyenda y flechas etiquetadas. Anotado que es imagen, no código como prefiere el curso                  |
| Escenarios alcanzables desde la fila de su aspecto            | `docs/aspectos.md` en `59590c9`                        | No cumple     | La fila de A-01 sigue con C4/ADR/Código/Pruebas/Evidencia en «Pendiente» y no hay enlaces a los escenarios                                                                                                                   |

### Matriz transversal

| Criterio                                                                 | Evidencia técnica                                                                                                                        | Estado    | Observaciones                                                                      |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | --------- | ---------------------------------------------------------------------------------- |
| Repositorio en la organización, con el nombre de la convención y público | `lsremote.txt:18`                                                                                                                        | Cumple    | —                                                                                  |
| Estructura mínima presente                                               | `git ls-tree -r 59590c9`: `README.md`, `docs/arc42/`, `docs/c4/C4-ContextoTAIA.png`, `docs/aspectos.md`, `docs/ia.md`; falta `docs/adr/` | No cumple | `docs/adr/` sigue sin existir (se crea el 22-ago, ya en semana 3)                  |
| Estado calificado identificable                                          | `59590c9243aad55222769426c45f6f7d4084572e` · `2026-08-16T19:15:15-05:00`                                                                 | Cumple    | Commit anterior al cierre, sin etiqueta                                            |
| Nombres de ADR según la convención                                       | No existe `docs/adr/`                                                                                                                    | Cumple    | Sin ADR al cierre                                                                  |
| ADR aceptados no reescritos                                              | Sin ADR al cierre                                                                                                                        | Cumple    | No aplica por ausencia                                                             |
| `docs/ia.md` al día para la semana                                       | commit `59590c9` (16-08) dentro del periodo; Entradas 001 y 002                                                                          | Cumple    | La Entrada 001 documenta lo rechazado con motivo; la 002 solo registra lo aceptado |
| Sin credenciales en el repositorio ni en el historial                    | `git grep` regex §9 sobre `59590c9`: sin coincidencias; sin `.env`; `git log -S'BEGIN PRIVATE KEY'`: vacío                               | Cumple    | —                                                                                  |
| Contribución de todos los integrantes                                    | `git shortlog -sne 59590c9`: val (2 identidades consolidadas), dei0811, luis20072002, mark                                               | Cumple    | Los 4 integrantes constan en el historial                                          |

**Resultado informado por el autocalificador: 3 de 9 criterios cumplidos, con 1 No verificado.**

## 3.2 Justificación

La Semana 2 es donde más se nota la diferencia entre el trabajo realizado y el conocimiento que teníamos de las métricas y convenciones del autocalificador.

### Aspectos que sí estaban cumplidos

La sección 1 de arc42 ya contenía objetivos de calidad, motivación, métricas e interesados. También existía una separación entre requisitos y restricciones, y se habían definido cinco escenarios de calidad.

Por tanto, no consideramos que la documentación estuviera ausente; el problema fue principalmente de **ubicación, precisión y cumplimiento de criterios formales**.

### Hallazgos originales

En S2 se identificaron:

* ausencia de una categoría legal explícita en la sección correspondiente de arc42;
* placeholders pendientes en la sección 3;
* ausencia de una medida numérica suficiente en el escenario de calidad S5;
* árbol de utilidad sin impacto/riesgo explícito;
* campos pendientes en `docs/aspectos.md`;
* ausencia de ADR;
* C4 marcado como No verificado por limitaciones de inspección visual.

Los estados históricos se mantienen como parte de la línea base de S2.

### Contraste con el estado actual

| Origen | Hallazgo                                   | Acción realizada                                      | Evidencia actual                         | Estado    |
| ------ | ------------------------------------------ | ----------------------------------------------------- | ---------------------------------------- | --------- |
| S2     | Sección de arc42 incompleta                | Se completó la documentación arquitectónica           | `docs/arc42/`                            | Corregido |
| S2     | Placeholders en arc42                      | Se completaron las vistas/documentación               | `docs/arc42/`                            | Corregido |
| S2     | Escenario de calidad sin medida suficiente | Se consolidaron los escenarios de calidad             | `docs/calidad/escenarios_calidad.md`     | Corregido |
| S2     | Árbol de utilidad incompleto               | Se actualizó la documentación de calidad              | `docs/calidad/`                          | Corregido |
| S2     | Trazabilidad de aspectos incompleta        | Se completó la fila A-01                              | `docs/aspectos.md`                       | Corregido |
| S2     | No existía ADR                             | Se incorporó ADR-0001                                 | `docs/adr/0001-estilo-arquitectonico.md` | Corregido |
| S2     | C4 no verificable visualmente              | Actualmente existen diagramas C4 en formato revisable | `docs/c4/`                               | Corregido |


### Punto discutible: C4 de contexto

El C4 fue marcado como **No verificado**, no como **No cumple**.

La razón indicada por el propio autocalificador es que el archivo `C4-ContextoTAIA.png` existía, pero el agente no podía inspeccionar visualmente la imagen.

Por tanto, consideramos importante que este resultado no se interprete como evidencia de que el diagrama era incorrecto. Simplemente no pudo ser comprobado automáticamente.

---

# 4. Semana 3

## 4.1 Tabla original de evaluación

| Criterio                                                                   | Evidencia técnica                                                            | Estado        | Observaciones                                                                                                                                                                                                             |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| arc42 sección 4 con estrategia y tácticas ligadas a los escenarios         | `docs/arc42/arc42-template-EN.md:250-306`                                    | Cumple        | 4.1-4.3: monolito modular + hexagonal selectivo; tabla de Quality-Driven Strategy liga S1-S5 a mecanismos concretos (autorización centralizada, puertos/adaptadores, módulo de recordatorios separado).                   |
| Matriz comparativa de los tres estilos contra el árbol de utilidad         | `docs/adr/0001.md:1-41`                                                      | Cumple        | Tabla capas/hexagonal/monolito modular contra S1-S5 del árbol (`docs/calidad/arbol_utilidad.md`) con justificación por escenario, no tabla genérica. Está en el ADR, no en arc42: se acepta, la ficha no exige ubicación. |
| `docs/adr/0001-*.md` con el nombre de la convención                        | `docs/adr/0001.md`                                                           | No cumple     | `0001.md` no sigue `NNNN-titulo-en-kebab-case.md` (filtro §4 del CONTRATO).                                                                                                                                               |
| ADR con contexto, opciones evaluadas, decisión y consecuencias             | `docs/adr/0001.md` (89 líneas)                                               | No cumple     | Sin título H1 que enuncie la decisión y sin sección de contexto; sí hay opciones (matriz + beneficios/costos), decisión y consecuencias.                                                                                  |
| Alternativas descartadas con su motivo                                     | `docs/adr/0001.md:53-63, 88-89`                                              | Cumple        | Microservicios descartado explícitamente con motivo; hexagonal completo rechazado en «Costos aceptados»; capas queda implícito en la matriz.                                                                              |
| ADR alcanzable desde `docs/aspectos.md` y desde el escenario que lo motiva | `docs/aspectos.md:6,26`; `docs/calidad/escenarios_calidad.md`                | No cumple     | `aspectos.md` enlaza a `adr/0001-estilo-arquitectonico.md` (no existe; el archivo es `0001.md`) y al escenario con `ruta/al/escenario.md` (placeholder). `escenarios_calidad.md` no enlaza al ADR.                        |
| Arranque con un solo comando documentado en el README                      | `README.md` («.\run.bat» desde la raíz); `run.bat` presente                  | Cumple        | `run.bat` contiene `python -m uvicorn backend.app.main:app --reload`. Ejecución real: **No verificado** (regla del kit: no se ejecuta código del estudiante); comando anotado.                                            |
| Prueba automatizada en verde                                               | `backend/tests/test_entrega3.py` (test_health)                               | No verificado | La prueba existe, pero no hay `.github/workflows/` (sin CI) y el repo no aporta evidencia de ejecución local. Haría falta un run de pipeline o captura de `pytest` con resultado.                                         |
| Estructura de paquetes correspondiente al estilo del ADR                   | `backend/app/modules/{academic,ai,reminders}/{domain,application,adapters}/` | Cumple        | Coincide con el ADR: monolito modular con organización hexagonal selectiva (domain/application/adapters por módulo).                                                                                                      |

### Matriz transversal

| Criterio                                                                 | Estado    | Observaciones                                                                                                                                     |
| ------------------------------------------------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repositorio en la organización, con el nombre de la convención y público | Cumple    | Clonado sin autenticación; nombre `AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant`.                                                       |
| Estructura mínima presente                                               | Cumple    | `README.md`, `docs/arc42/`, `docs/adr/`, `docs/c4/`, `docs/aspectos.md`, `docs/ia.md` en el hash calificado.                                      |
| Estado calificado identificable                                          | Cumple    | `46257a03` · 2026-08-23T16:47:00-05:00, último commit ≤ cierre; sin etiqueta (evidencia semanal).                                                 |
| Nombres de ADR según la convención                                       | No cumple | `docs/adr/0001.md` no pasa el filtro `^[0-9]{4}-[a-z0-9]+(-[a-z0-9]+)*\.md$`.                                                                     |
| ADR aceptados no reescritos                                              | Cumple    | `git log --follow -- docs/adr/0001.md` → un solo commit (`decaa36`, 2026-08-22), sin reescrituras posteriores.                                    |
| `docs/ia.md` al día para la semana                                       | No cumple | Commits dentro del periodo (`e977adb` 08-23), pero la Entrada 03 (ClaudeCode, 08-23) está incompleta: sin «Aceptado» ni «Rechazado o modificado». |
| Sin credenciales en el repositorio ni en el historial                    | Cumple    | `git grep` §9 sin coincidencias; sin `.env` versionado.                                                                                           |
| Contribución de todos los integrantes                                    | Cumple    | 4 identidades consolidadas: val (2 correos), dei0811, luis20072002, mark = los 4 integrantes del equipo.                                          |

**Resultado informado por el autocalificador: 5 de 9 criterios cumplidos.**

## 4.2 Justificación

La Semana 3 debe analizarse teniendo en cuenta el contexto de que **el autocalificador fue incorporado aproximadamente un día antes de esta semana**.

Esto es relevante porque fue a partir de este momento cuando el equipo comenzó a conocer con mayor precisión convenciones como:

* el formato obligatorio para nombres de ADR;
* la necesidad de trazabilidad;
* la forma esperada de relacionar aspectos, escenarios, C4 y ADR;
* la necesidad de evidencia automatizada para considerar una prueba como verde;
* los requisitos formales del registro de IA.

### Aspectos que el autocalificador reconoció como cumplidos

La estrategia arquitectónica sí estaba documentada y relacionada con los escenarios S1-S5. También existía una matriz comparativa de estilos arquitectónicos y la estructura de paquetes correspondía con la decisión tomada.

Esto demuestra que la arquitectura no era únicamente una intención: ya existía una correspondencia entre la decisión arquitectónica y la estructura del proyecto.

### Hallazgos originales

En S3 se identificaron:

* nombre incorrecto del archivo ADR;
* estructura incompleta del ADR;
* enlaces y placeholders pendientes;
* entrada de IA incompleta;
* ausencia de integración continua;
* pruebas cuyo resultado no podía verificarse mediante CI.

### Correcciones realizadas

| Origen | Hallazgo                         | Acción realizada                                                | Evidencia actual                              | Estado    |
| ------ | -------------------------------- | --------------------------------------------------------------- | --------------------------------------------- | --------- |
| S3     | Nombre incorrecto del ADR        | Se renombró el ADR siguiendo la convención                      | `docs/adr/0001-estilo-arquitectonico.md`      | Corregido |
| S3     | ADR incompleto                   | Se completaron contexto, alternativas, decisión y consecuencias | ADR-0001                                      | Corregido |
| S3     | Enlaces/placeholders pendientes  | Se actualizaron los documentos relacionados                     | `docs/arc42/`, `docs/c4/`, `docs/aspectos.md` | Corregido |
| S3     | Registro de IA incompleto        | Se ampliaron las entradas del registro                          | `docs/ia.md`                                  | Corregido |
| S3     | No existía CI                    | Se incorporó GitHub Actions                                     | `.github/workflows/`                          | Corregido |
| S3     | Pruebas sin evidencia automática | Se configuró pytest dentro del pipeline                         | `.github/workflows/`, `backend/tests/`        | Corregido |

---

# 5. Semana 4

## 5.1 Tabla original de evaluación

| Criterio de evaluacion                                             | Evidencia tecnica                                                                                                                 | Estado        | Observaciones                                                                                                                                       |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| arc42 secciones 1 a 6 redactadas, sin texto de plantilla           | docs/arc42/arc42-template-EN.md (secciones 1-2 visibles); commit 0152345 actualiza 5, 6, 10 y 12                                  | No verificado | Contenido de secciones 3-4 no inspeccionable en la evidencia; falta ejecutar grep de plantilla.                                                     |
| arc42 sección 9 al día y enlazada con los ADR existentes           | Sin contenido visible de la sección 9 en la evidencia                                                                             | No verificado | Falta inspeccionar la sección 9 y su enlace a docs/adr/0001-estilo-arquitectonico.md.                                                               |
| arc42 sección 10 coherente con los escenarios de la semana 2       | Commit 0152345 actualiza sección 10; escenarios en docs/calidad/escenarios_calidad.md                                             | No verificado | Sin el texto de la sección 10 no se confirma la coherencia con S1-S5.                                                                               |
| Glosario iniciado con términos del dominio                         | Commit 0152345 inicia sección 12 de arc42                                                                                         | No verificado | Sin el texto del glosario no se confirman términos propios del sistema.                                                                             |
| C4 nivel 1 y nivel 2 presentes y coherentes entre sí               | docs/c4/C4-C1.md y docs/c4/C4-C2.md (hash c087303)                                                                                | Cumple        | Actor estudiante y sistemas externos Telegram/LLM coherentes entre niveles; flechas etiquetadas y leyenda; diagramas como código Mermaid.           |
| Límites del C4 nivel 2 correspondientes a la estructura del código | docs/c4/C4-C2.md vs árbol backend/                                                                                                | Cumple        | API TAIA corresponde a backend/app/modules/academic/adapters/api.py; App Móvil y Base de Datos dibujadas sin código (objetivo declarado en README). |
| Corte vertical que atraviesa interfaz, lógica y persistencia       | backend/app/modules/academic/adapters/api.py, application/register_task.py, adapters/in_memory_task_repository.py, domain/task.py | Cumple        | Recorrido HTTP → caso de uso → dominio → persistencia en memoria.                                                                                   |
| Arranque documentado con un solo comando                           | README.md sección Requisitos/Ejecución; run.bat en el árbol                                                                       | Cumple        | Comando declarado: .\run.bat; no se ejecutó por ausencia de runs_ci.                                                                                |
| Prueba automatizada del recorrido completo, en verde               | backend/tests/test_academic_register_task.py existe; runs_ci vacío                                                                | No verificado | Sin run en verde; docs/ia.md entrada 05 declara pendiente ejecutar pytest.                                                                          |
| Fila de docs/aspectos.md completa hasta la columna Pruebas         | docs/aspectos.md fila A-01 (hash c087303)                                                                                         | Cumple        | Celdas ID→Evidencia verificadas; todas las rutas existen en el árbol.                                                                               |

### Matriz transversal

| Criterio                               | Evidencia                                                                                                                  | Estado    | Observaciones                                                                                   |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------- |
| Identidad del repositorio              | repo AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant en ISCOUTB, visible; autores: val, dei0811, mark, luis20072002 | Cumple    | 4 identidades consolidadas coinciden con los integrantes declarados.                            |
| Estructura mínima                      | docs/arc42/, docs/adr/, docs/c4/, docs/aspectos.md, docs/ia.md, README.md presentes                                        | Cumple    | arc42 en un solo archivo; desviación menor permitida por la ficha.                              |
| Estado del repositorio que se califica | c087303 2026-08-30T18:54:10-05:00 anterior al cierre 2026-08-31T05:00:00Z; sin commits post cierre                         | Cumple    | Sin etiqueta, pero es evidencia semanal y el commit es anterior al cierre.                      |
| Convenciones de ADR                    | docs/adr/0001-estilo-arquitectonico.md existe y nombra la decisión                                                         | No cumple | Falta sección de trazabilidad (requisito/aspecto, C4, commit, pruebas) exigida por el contrato. |
| Tabla de aspectos                      | docs/aspectos.md fila A-01 con 8 columnas y rutas verificadas                                                              | Cumple    | Cadena aspecto→requisito→C4→ADR→código→pruebas→evidencia navegable.                             |
| Registro de uso de IA                  | docs/ia.md con entradas 001-005, cada una con aceptado/rechazado y verificación                                            | Cumple    | Log crece de 2026-08-06 a 2026-08-30.                                                           |
| README                                 | README.md con descripción, requisitos, comando .\run.bat y pytest backend/tests                                            | Cumple    | Ejecución no verificada por ausencia de runs_ci.                                                |
| Pipeline y análisis estático           | Sin .github/workflows/ en el árbol; runs_ci vacío                                                                          | No cumple | No hay CI en cada push ni SonarCloud; sin enlace a run alternativo.                             |

**Resultado informado por el autocalificador: 5 de 10 criterios cumplidos.**

## 5.2 Justificación

La Semana 4 es particularmente importante porque ya existía una parte funcional considerable del proyecto.

El autocalificador reconoció como cumplidos:

* C4 nivel 1 y nivel 2;
* correspondencia entre C4 y estructura de código;
* corte vertical funcional;
* arranque mediante un solo comando;
* tabla de aspectos completa.

El corte vertical estaba compuesto por:

`HTTP → caso de uso → dominio → persistencia`

con `api.py`, `register_task.py`, `Task` e `InMemoryTaskRepository`. El propio autocalificador lo reconoció como **Cumple**.

### Punto fundamental: arc42 marcado como No verificado

Los cuatro primeros criterios de la Semana 4 fueron marcados **No verificado**.

Esto debe diferenciarse de un **No cumple**.

La evidencia del autocalificador indica que el agente no pudo inspeccionar completamente el contenido de las secciones correspondientes. Por ejemplo, para la sección 10 se reconoce que el commit `0152345` actualizaba dicha sección, pero se indicó que no se podía confirmar su coherencia con S1-S5.

Por tanto, **no consideramos correcto utilizar esos cuatro No verificado como evidencia de que las secciones estaban ausentes o incorrectas**.

En el estado del proyecto ya existía contenido en esas secciones y posteriormente se continuó corrigiendo y completando la documentación.

### Hallazgos originales

En S4 se identificaron:

* secciones de arc42 que no podían verificarse completamente;
* trazabilidad incompleta del ADR;
* ausencia de pipeline de integración continua;
* pruebas automatizadas cuyo resultado no podía contrastarse mediante CI;
* aspectos y corte vertical que sí presentaban evidencia favorable.

### Contraste con el estado actual

| Origen | Hallazgo                        | Acción realizada                                                                     | Evidencia actual                         | Estado    |
| ------ | ------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------- | --------- |
| S4     | Arc42 parcialmente verificable  | Se completaron las vistas arquitectónicas                                            | `docs/arc42/`                            | Corregido |
| S4     | Trazabilidad del ADR incompleta | Se incorporó una sección de trazabilidad                                             | `docs/adr/0001-estilo-arquitectonico.md` | Parcial   |
| S4     | No existía CI                   | Se incorporó GitHub Actions                                                          | `.github/workflows/`                     | Corregido |
| S4     | Pruebas sin evidencia de CI     | Las pruebas se incorporaron al pipeline                                              | `.github/workflows/`, `backend/tests/`   | Corregido |
| S4     | Aspecto A-01 con trazabilidad   | Se consolidó la cadena aspecto → requisito → C4 → ADR → código → pruebas → evidencia | `docs/aspectos.md`                       | Corregido |
| S4     | Corte vertical                  | Se mantiene el incremento A-01 de registro y consulta de tareas                      | `backend/app/modules/academic/`          | Corregido |


---

# 6. Evolución del proyecto después de las evaluaciones

Los resultados del autocalificador fueron utilizados como retroalimentación para mejorar el proyecto.

Entre las correcciones realizadas se encuentran:

* Renombramiento del ADR para cumplir la convención establecida.
* Corrección de enlaces entre aspectos, ADR y escenarios.
* Incorporación de trazabilidad al ADR-0001.
* Completitud progresiva de `docs/ia.md`.
* Consolidación de los escenarios de calidad.
* Construcción de C4 nivel 1 y nivel 2 como diagramas Mermaid.
* Implementación de un corte vertical funcional del módulo académico.
* Incorporación de pruebas automatizadas para el registro y consulta de tareas.
* Documentación de la ejecución mediante `run.bat`.
* Configuración de GitHub Actions para ejecutar las pruebas.
* Corrección de la configuración de pytest para que CI pudiera importar correctamente el paquete `backend`.
* Verificación posterior de las pruebas, obteniendo **9 pruebas exitosas**.

El proyecto pasó, por tanto, de una documentación inicial incompleta a una arquitectura con una primera funcionalidad vertical ejecutable y evidencia automatizada.

---

# 7. Matriz transversal de correcciones

Esta matriz consolida los principales hallazgos que deben contrastarse para el Corte 1.

| Origen | Hallazgo / fila                       | Respuesta en `correcciones.md`                                           | Evidencia contrastada                                        | Resultado |
| ------ | ------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------ | --------- |
| S1     | No existían `docs/adr/` ni `docs/c4/` | Se incorporaron ambas estructuras                                        | `docs/adr/`, `docs/c4/`                                      | Corregido |
| S1     | Tensiones de calidad no explícitas    | Se consolidó la documentación de escenarios y decisiones arquitectónicas | `docs/arc42/`, `docs/calidad/`, `docs/adr/`                  | Corregido |
| S1     | Contribución inicial limitada         | Los cuatro integrantes aparecen posteriormente en el historial           | Historial Git                                                | Corregido |
| S2     | Restricciones sin categoría legal     | Se completó la documentación arquitectónica                              | `docs/arc42/`                                                | Corregido |
| S2     | Sección 3 con placeholders            | Se completó la vista de contexto                                         | `docs/arc42/`, `docs/c4/`                                    | Corregido |
| S2     | Escenario S5 sin métrica              | Se consolidaron los escenarios de calidad                                | `docs/calidad/escenarios_calidad.md`                         | Corregido |
| S2     | Árbol de utilidad sin priorización    | Se actualizó la documentación de calidad                                 | `docs/calidad/arbol_utilidad.md`                             | Corregido |
| S2     | C4 de contexto No verificado          | Se dispone actualmente de C4 documentado como código                     | `docs/c4/`                                                   | Corregido |
| S2     | Aspecto A-01 incompleto               | Se completaron las relaciones arquitectónicas                            | `docs/aspectos.md`                                           | Corregido |
| S3     | Nombre incorrecto de ADR              | Se renombró el archivo                                                   | `docs/adr/0001-estilo-arquitectonico.md`                     | Corregido |
| S3     | ADR incompleto                        | Se completó su estructura                                                | `docs/adr/0001-estilo-arquitectonico.md`                     | Corregido |
| S3     | Enlaces incorrectos                   | Se actualizaron las referencias                                          | `docs/aspectos.md`, `docs/calidad/`                          | Corregido |
| S3     | IA-03 incompleto                      | Se completó el registro correspondiente                                  | `docs/ia.md`                                                 | Corregido |
| S3     | Sin CI                                | Se incorporó GitHub Actions                                              | `.github/workflows/`                                         | Corregido |
| S3     | Prueba No verificada                  | Se habilitó ejecución automatizada                                       | `backend/tests/`, CI                                         | Corregido |
| S4     | Arc42 parcialmente No verificado      | Se completaron y consolidaron las vistas arquitectónicas                 | `docs/arc42/`                                                | Corregido |
| S4     | Prueba sin evidencia de ejecución     | Se incorporó pipeline automatizado                                       | `.github/workflows/`                                         | Corregido |
| S4     | Falta de trazabilidad del ADR         | Se incorporó trazabilidad y referencias cruzadas                         | `docs/adr/0001-estilo-arquitectonico.md`, `docs/aspectos.md` | Corregido |
| S4     | Falta de pipeline                     | Se configuró GitHub Actions                                              | `.github/workflows/`                                         | Corregido |

---

# Conclusión

Las evaluaciones de S1–S4 muestran una evolución progresiva del proyecto desde una documentación arquitectónica inicial hasta una línea base con documentación, decisiones arquitectónicas, vistas C4, trazabilidad, implementación vertical, pruebas automatizadas y pipeline de integración.

Los incumplimientos históricos identificados por el autocalificador se conservan en este documento y no se presentan como si nunca hubieran existido. La finalidad de las correcciones posteriores es demostrar cómo cada hallazgo fue atendido y cuál es la evidencia disponible en el estado actual.

Para el Corte 1, el repositorio se presentará sobre una línea base única e identificable mediante la etiqueta `corte-1`, acompañada por este documento de correcciones, la documentación arquitectónica y la evidencia técnica correspondiente.

El objetivo de este documento es, por tanto, dejar una **trazabilidad navegable entre hallazgo → corrección → evidencia → estado**, permitiendo contrastar el estado histórico con el estado consolidado del proyecto.
