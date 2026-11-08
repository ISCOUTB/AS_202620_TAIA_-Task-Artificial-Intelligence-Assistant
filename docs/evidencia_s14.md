# Evidencia S14 · Medición de atributos de calidad

| | |
|---|---|
| `idnumber` en Moodle | `arqsw:evidencia-s14` |
| Semana | 14 |
| Corte | Tercer corte |
| Tipo | grupal, nota única del equipo |
| Commit revisado | `023dc7fc3da6bbf064800e8d900cc58da35e9846` |
| Fecha del commit | 2026-11-01T10:38:30-05:00 |
| Fecha de la revisión | 2026-11-08 |

> El commit revisado es el `HEAD` de `main` en la fecha de la revisión. Si el cierre de la
> actividad fija otro commit, la matriz se repite sobre ese.

## Escenarios medidos y umbrales (arc42 §10)

| Escenario | Umbral declarado en [§10](arc42/10-requisitos-de-calidad.md) | Umbral usado en la medición |
|---|---|---|
| S1 — Registro correcto | ≥ 90 % de los campos esperados, identificados y registrados, en 100 mensajes | ≥ 90 % (igual) |
| S3 — Respuesta del asistente | p95 ≤ 7 s, desde la recepción en el backend hasta el envío al canal | p95 ≤ 7 000 ms (igual) |

El umbral no cambió entre §10 y la medición, así que no hace falta ADR que lo justifique.

## Procedimiento y resultado

| | |
|---|---|
| Herramienta | [`tools/eval_llm.py`](../tools/eval_llm.py) sobre [`dataset.jsonl`](evaluacion_ia/dataset.jsonl) |
| Carga | 100 casos (99 evaluables; `x002` excluido por vacío), 110 campos etiquetados, llamadas secuenciales con 6 s de pausa |
| Repeticiones | una corrida por configuración: Gemini 2026-10-05; Groq, Groq con día y Gemini con día 2026-10-31 |
| Entorno | equipo del estudiante, contra la API real del proveedor; declarado en [contraste_umbrales.md](evaluacion_ia/contraste_umbrales.md) y en [§11.1](arc42/11-riesgos-y-deudas-tecnicas.md#111-integraciones-externas-y-funcionalidades-pendientes) |
| Resultado S1 (extracción) | **91,8 %** (101/110) frente a 90 %: cumple en la extracción. Gemini con día, 2026-10-31: 95,5 % (105/110) |
| Resultado S1 (registro) | no medido: el arnés no confirma ni persiste |
| Resultado S3 (tramo del modelo) | p95 **2 191,0 ms** frente a 7 000 ms: cumple en ese tramo; máximo 20 209,5 ms (timeout) |
| Resultado S3 (extremo a extremo) | no medido en el despliegue; una observación aislada en producción de 9 337 ms ([§11.14](arc42/11-riesgos-y-deudas-tecnicas.md#1114-latencia-del-asistente-cuando-responde-el-respaldo)) |

## Matriz de cumplimiento

| Criterio de evaluación | Evidencia técnica esperada | Estado (Cumple / No cumple) | Observaciones |
|---|---|---|---|
| Escenario medido identificado, con el umbral declarado en arc42 sección 10 | escenario citado y su umbral | **Cumple** | [contraste_umbrales.md](evaluacion_ia/contraste_umbrales.md) cita S1 (≥ 90 % de campos en 100 mensajes) y S3 (p95 ≤ 7 s), con los mismos valores de [§10.2](arc42/10-requisitos-de-calidad.md#102-escenarios-de-calidad). No se inventó un umbral nuevo. |
| Procedimiento de medición con herramienta, carga y repeticiones | script o apartado del procedimiento | **Cumple** | Herramienta `tools/eval_llm.py`, carga de 99 mensajes y 110 campos, pausa de 6 s entre llamadas, comandos en el apartado «Reproducción». Débil en repeticiones: hay **una sola corrida** por configuración, sin repetir la misma para ver la variación, y la carga es secuencial, no concurrente. |
| Medición reproducible por otra persona | artefactos versionados de la medición | **Cumple** | Están versionados el arnés, el conjunto, las etiquetas y los JSON con `procedencia` (commit base, hash del conjunto y del arnés, modelo, reloj fijo). Límites: todas las corridas registran `arbol_modificado: true`, así que el commit base no reproduce exactamente el código medido, y hace falta una clave propia de Gemini o Groq. |
| Resultado contrastado con el umbral, con conclusión explícita | cifra obtenida frente al umbral | **Cumple** | Tabla «Contraste» con conclusión por tramo: S1 extracción 91,8 % frente a 90 %, **supera**; S1 registro **no verificado**; S3 tramo del modelo p95 2 191 ms frente a 7 000 ms, **dentro**; S3 extremo a extremo **no verificado**. Dice que S1 completo no queda demostrado. Las corridas del 2026-10-31 (Groq y Gemini con día) solo están en [modelo_amenazas.md](modelo_amenazas.md), no en el contraste. |
| Entorno de la medición declarado | apartado que dice si fue local o desplegado | **Cumple** | Declara que S3 se midió «desde el equipo del estudiante» y que el recorrido desplegado no se ejercitó (§11.1). Así, el p95 es del tramo del modelo medido en local, no la latencia del sistema desplegado que pide S3. Aparte, S4 sí se midió sobre el despliegue ([aislamiento_c9dae4fb4f.json](evaluacion_ia/aislamiento_c9dae4fb4f.json), 100/100). |
| arc42 sección 11 con lo señalado por los pares | `docs/arc42/11*` y su historial | **No aplica** | El docente no realizó la revisión entre pares (`arqsw:workshop-pares`), así que el equipo no recibió señalamientos que incorporar. [§11](arc42/11-riesgos-y-deudas-tecnicas.md) sigue vigente como registro de riesgos y deudas; el último commit que la toca es `a71937d` (2026-10-30). |
| Estado de cada señalamiento: corregido, asumido o pendiente | columna o apartado de estado | **No aplica** | Sin revisión entre pares no hay señalamientos que clasificar. |
| Columna de evidencia del aspecto medido, apuntando a esta medición | fila de `docs/aspectos.md` | **Cumple** | La fila A-03 de [aspectos.md](aspectos.md) enlaza [resultado_s1_100.json](evaluacion_ia/resultado_s1_100.json) (91,8 %, p95 2 191,0 ms) y [contraste_umbrales.md](evaluacion_ia/contraste_umbrales.md). No enlaza los resultados del 2026-10-31. |

## Cierre

Recuento: **6 de 6 criterios aplicables cumplidos.** Los 2 criterios de la revisión entre pares no
aplican, porque el docente no realizó esa actividad.

Nota sugerida: `1 + 4 × (6/6)` = **5,0**. Si el docente decide contar las 8 filas de la matriz,
sería `1 + 4 × (6/8)` = 4,0. Es una propuesta al docente; la nota final la fija el profesor en
Moodle.

> No se rellenó la matriz transversal de `CONTRATO.md`: ese archivo no está en el repositorio.

### Pendiente antes del proyecto final

1. **S3 extremo a extremo en el despliegue.** Medir `POST /ai/message` en el entorno de Dokploy
   (`GET /metrics`, p95 sobre una muestra suficiente) y concluir frente a los 7 s. Hoy solo
   se midió el tramo del modelo, en local.
2. **S1 sobre lo registrado.** Medir los campos persistidos tras la confirmación, no solo los
   extraídos.
3. **Repeticiones y árbol limpio.** Repetir al menos una configuración varias veces y ejecutarla
   sobre un commit sin cambios locales (`arbol_modificado: false`).
4. **Contraste al día.** Incorporar las corridas del 2026-10-31 a
   [contraste_umbrales.md](evaluacion_ia/contraste_umbrales.md) y a la fila A-03.
5. **arc42 completo con glosario.** [§12](arc42/12-glosario.md) sigue describiendo el primer
   corte («InMemoryTaskRepository», PostgreSQL «previsto», Flutter «no implementada»). Faltan
   Groq, Dokploy, Supabase, `LLMError`, acción pendiente, p95 y los escenarios S1–S5.
6. **C4 de los tres niveles.** Ya existen [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) y
   [C4-C3](c4/C4-C3.md). Hay que comprobar que reflejan el despliegue actual (Dokploy y Groq de
   respaldo).
7. **Tabla de aspectos recorrible de punta a punta.** A-06 sigue describiendo repositorios en
   memoria, aunque §11.2 da la persistencia en PostgreSQL por resuelta. A-01 y A-04 dicen que
   Gemini y PostgreSQL están pendientes. A-07 está fuera de la tabla principal (hay una línea
   en blanco que la separa). Ningún aspecto enlaza S2, que no tiene medición.
