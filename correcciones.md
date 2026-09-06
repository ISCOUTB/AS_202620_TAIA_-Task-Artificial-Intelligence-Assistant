# Justificación de la calificación de las semanas 1 a 4

## 1. Objetivo del documento

El presente documento tiene como objetivo justificar, con base en la evidencia generada por el autocalificador, la calificación obtenida por el proyecto **TAIA — Task Artificial Intelligence Assistant** durante las semanas 1 a 4.

La intención no es desconocer los incumplimientos identificados por el autocalificador. Por el contrario, se reconocen aquellos aspectos que efectivamente estaban incompletos y se diferencian de aquellos que fueron marcados como **No verificado**, ya que este estado no significa que el criterio estuviera incumplido, sino que el agente de evaluación no contó con evidencia suficiente para comprobarlo.

También se tiene en cuenta una circunstancia importante del proceso: **el equipo fue incorporado al autocalificador aproximadamente un día antes de la Semana 3**. Por esta razón, durante las primeras semanas no se conocían con suficiente anticipación todas las métricas, convenciones y criterios específicos utilizados posteriormente por el sistema automático de evaluación. A partir de la incorporación al autocalificador, sus resultados comenzaron a utilizarse como retroalimentación para corregir progresivamente el repositorio.

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

### Incumplimientos que aceptamos

Hay dos incumplimientos claros:

1. **No se habían declarado explícitamente dos tensiones de calidad.**
2. **Todavía no existían `docs/adr/` ni `docs/c4/`.**

También es correcto que, al cierre de S1, la contribución visible en el historial correspondiera solamente a una persona.

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

### Incumplimientos que aceptamos

Aceptamos los siguientes puntos:

* La sección 2 no tenía una categoría legal.
* La sección 3 todavía conservaba contenido de plantilla.
* El escenario S5 no tenía una métrica numérica.
* El árbol de utilidad no expresaba impacto y riesgo.
* `docs/aspectos.md` todavía tenía campos pendientes.
* `docs/adr/` todavía no existía al cierre.

Estos hallazgos están explícitamente registrados en la evaluación de S2.

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

### Incumplimientos que aceptamos

Aceptamos que en ese momento:

* el ADR se llamaba `0001.md` en lugar de seguir la convención completa;
* faltaban un título H1 y una sección explícita de contexto;
* había enlaces incorrectos o placeholders;
* la entrada 03 de `docs/ia.md` estaba incompleta;
* todavía no existía CI.

Estos son errores reales del estado evaluado.

### No verificado no significa No cumple

El test automatizado merece una consideración especial.

El autocalificador encontró que `backend/tests/test_entrega3.py` existía, pero lo marcó **No verificado** porque no había CI ni evidencia de ejecución local.

Por lo tanto, el resultado no demuestra que el test fallara. Demuestra únicamente que **no había evidencia suficiente para demostrar que había pasado**.

Este punto posteriormente fue solucionado mediante la incorporación de CI.

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

### Incumplimiento que sí aceptamos: trazabilidad del ADR

En el hash evaluado todavía faltaba la sección de trazabilidad del ADR-0001.

Este sí es un incumplimiento objetivo del contrato y posteriormente fue corregido incorporando trazabilidad hacia:

* requisitos;
* escenarios;
* C4;
* código;
* pruebas;
* evidencia.

Por tanto, este punto sí debe considerarse como un error real del estado evaluado, pero también como un punto que fue **identificado y corregido posteriormente**.

### CI y pruebas

En la Semana 4 el autocalificador marcó como No verificada la prueba del recorrido completo porque no había evidencia de un `runs_ci` en verde.

La prueba sí existía:

`backend/tests/test_academic_register_task.py`

pero no había evidencia automática que permitiera afirmar que había pasado.

Posteriormente se incorporó el pipeline de GitHub Actions y se corrigió la configuración de pytest. La ejecución local posteriormente mostró:

```text
9 passed
```

y el pipeline de CI quedó finalmente en verde.

Esto demuestra que el problema era principalmente **de evidencia de ejecución**, no de inexistencia del recorrido ni de ausencia de pruebas.

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

# 7. Diferencia entre "No cumple" y "No verificado"

Consideramos importante que la calificación tenga en cuenta esta diferencia.

| Estado            | Interpretación                                            | Cómo debería considerarse                  |
| ----------------- | --------------------------------------------------------- | ------------------------------------------ |
| **Cumple**        | El autocalificador encontró evidencia suficiente          | Se acepta como cumplimiento                |
| **No cumple**     | Se encontró evidencia de que el criterio no se satisfacía | Se acepta como incumplimiento              |
| **No verificado** | El agente no pudo comprobar el criterio                   | No demuestra que el proyecto estuviera mal |

Esto es especialmente relevante en:

* C4 de contexto de S2;
* ejecución del test en S3;
* varias secciones de arc42 en S4;
* ejecución del recorrido completo en S4.

Por ejemplo, que el agente no pudiera inspeccionar un PNG no significa que el C4 estuviera incorrecto. Del mismo modo, que no existiera todavía un `runs_ci` no significa que el test fallara.

---

# 8. Consideración sobre el proceso de evaluación

El equipo reconoce que durante las primeras semanas hubo aspectos que pudieron haberse desarrollado mejor y que algunos incumplimientos son responsabilidad del equipo.

Sin embargo, también consideramos relevante el momento en que se incorporó el autocalificador.

El equipo fue incorporado al sistema de evaluación aproximadamente **un día antes de la Semana 3**. Esto significó que durante S1 y S2 se trabajó sin conocer con suficiente anticipación el conjunto completo de métricas, convenciones y reglas que posteriormente serían utilizadas para determinar los estados de cumplimiento.

Por ejemplo, posteriormente descubrimos que aspectos como:

* el patrón exacto del nombre de un ADR;
* la trazabilidad requerida;
* la necesidad de evidencia de ejecución mediante CI;
* la métrica numérica obligatoria para cada escenario;
* la forma esperada del árbol de utilidad;

tenían un peso específico en la evaluación automática.

El hecho de que estos aspectos fueran descubiertos con tan poca anticipación explica parte de los errores formales observados en S2 y S3.

No se pretende que esta circunstancia elimine los incumplimientos. Se plantea como **contexto para interpretar la magnitud de la calificación**, especialmente cuando posteriormente se evidencia que el equipo reaccionó a la retroalimentación y corrigió los problemas identificados.

---

# 9. Valoración de la nota

La Semana 4 fue evaluada con **5 de 10 criterios cumplidos**, a partir de lo cual el autocalificador propuso una nota de **3.0** mediante la fórmula indicada en su reporte:

> `3.0 = 1 + 4 × (5/10)`

No cuestionamos que existieran incumplimientos en el estado evaluado. Sin embargo, consideramos que la nota debe analizarse teniendo en cuenta tres elementos:

### 1. Existía una funcionalidad arquitectónica real

Para S4 el autocalificador reconoció como cumplido el corte vertical, la correspondencia con C4, el arranque documentado y la tabla de aspectos. Esto significa que el proyecto ya contaba con una primera implementación coherente entre arquitectura, código y documentación.

### 2. Algunos resultados negativos eran No verificado

Cuatro criterios de la matriz principal de S4 fueron marcados como **No verificado**, no como **No cumple**.

Por tanto, no debería interpretarse que el proyecto fallaba en esos cuatro puntos.

### 3. Hubo una evolución verificable

Los problemas detectados por el autocalificador fueron utilizados para realizar correcciones posteriores, especialmente en:

* ADR;
* trazabilidad;
* pruebas;
* CI;
* estructura de documentación;
* relación entre arquitectura y código.

Esto evidencia un proceso de aprendizaje y adaptación al criterio de evaluación.

---

# 10. Conclusión

Consideramos que la evaluación del proyecto debe reconocer tanto los incumplimientos reales como el estado de evolución del trabajo.

En las semanas 1 y 2 existían deficiencias importantes de documentación y estructura, las cuales reconocemos. Sin embargo, parte de estas deficiencias se produjeron antes de que el equipo tuviera acceso suficiente al funcionamiento y a las métricas específicas del autocalificador.

En la Semana 3, el equipo ya había comenzado a adaptar el proyecto a los criterios de evaluación, incorporando ADR, estructura modular y una estrategia arquitectónica explícita.

En la Semana 4 se alcanzó un punto más significativo: existía un **corte vertical funcional**, pruebas automatizadas, C4 coherente, trazabilidad de aspectos y una arquitectura documentada. Los principales pendientes estaban relacionados con evidencia automática, trazabilidad adicional y CI.

Por estas razones, consideramos que una calificación basada exclusivamente en el número de criterios marcados como `Cumple` puede subestimar el estado real del proyecto, especialmente cuando varios criterios fueron clasificados como `No verificado` y posteriormente fueron demostrados o corregidos.

Nuestra posición no es que el proyecto haya cumplido todo desde el principio, sino que **la calificación debería considerar la diferencia entre incumplimientos reales, aspectos no verificables automáticamente y la evolución demostrable del proyecto durante las cuatro semanas**.

El resultado final de TAIA muestra una progresión desde una documentación inicial hasta una arquitectura con una implementación vertical funcional, pruebas automatizadas y un proceso de mejora basado en la retroalimentación obtenida.

**Por lo anterior, solicitamos que la calificación sea reconsiderada teniendo en cuenta tanto la evidencia de cada semana como el contexto de incorporación tardía al autocalificador y la evolución posterior del proyecto.**
