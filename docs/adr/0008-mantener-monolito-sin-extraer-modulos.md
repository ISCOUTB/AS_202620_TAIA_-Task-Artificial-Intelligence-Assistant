# ADR-0008 — Mantener el monolito modular sin extraer módulos a servicios

## Estado

Aceptado por el equipo el 2026-10-18.

## Contexto

[ADR-0001](0001-estilo-arquitectonico.md) eligió un monolito modular y descartó los microservicios
**para la etapa inicial**, dejando abierta la extracción de un módulo "si en el futuro algún módulo
alcanza un nivel de complejidad o carga que justifique separarlo". [arc42 §11.8](../arc42/11-riesgos-y-deudas-tecnicas.md)
registra el despliegue único como deuda técnica, pero sin criterios para decidir cuándo dejaría de
serlo.

Con el análisis de fallos parciales de la semana 11 ([modos_fallo_s11.md](../modos_fallo_s11.md))
la pregunta se puede responder con criterios: qué ganaría y qué perdería TAIA si un módulo pasara a
ser un servicio propio, y si alguna de esas ganancias hace falta hoy.

Estado actual de los módulos, verificado sobre `backend/app/modules`:

| Módulo | Depende de otro módulo | Mediante |
|---|---|---|
| `ai` | `academic` | Puerto `AcademicTaskManagement` (`academic/application/ports/inbound/task_management`) |
| `reminders` | `usuario`, `academic` | Puerto `IdentityService`; consulta de tareas con `AcademicTaskLookup`, conectada en `main.py` |
| `academic` | Ninguno | |
| `usuario` | Ninguno | Lo usan los demás para identificar al estudiante |

No hay claves foráneas entre tablas de módulos distintos ([propiedad_datos_s6.md](../propiedad_datos_s6.md)),
y las fronteras se comprueban en las pruebas ([`test_s8_closure.py`](../../backend/tests/test_s8_closure.py)).
Es decir: las fronteras permitirían extraer un módulo. Lo que este ADR decide es si conviene.

## Escenarios de calidad relacionados

- **S3 — Respuesta del asistente ante un mensaje** (p95 ≤ 7 s,
  [escenarios_calidad.md](../calidad/escenarios_calidad.md)): toda llamada de red nueva en el camino
  de `POST /ai/message` suma latencia.
- **S1 — Registro correcto de información académica:** una escritura repartida entre servicios
  puede quedar a medias.

## Criterios de decisión

| Criterio | Pregunta | Evidencia |
|---|---|---|
| Carga y escalado | ¿Hay un módulo que necesite más recursos que el resto? | 0,2 peticiones por segundo en la hora pico y 1 000 llamadas al LLM por día ([costo_mensual.md, §1](../costo_mensual.md)). |
| Aislamiento de fallos | ¿Un fallo de un módulo tumba a los demás? | Un fallo de Gemini se traduce a `LLMError` y el resto de la API sigue atendiendo ([ADR-0007](0007-comportamiento-ante-fallo-del-proveedor-llm.md), `RNF-09`). El fallo dominante es el límite de cadencia de Gemini ([arc42 §11.6](../arc42/11-riesgos-y-deudas-tecnicas.md)), que ocurre fuera de TAIA. |
| Consistencia de datos | ¿Aparece una transacción repartida entre servicios? | Hoy no: un proceso, una base de datos y escrituras locales ([modos_fallo_s11.md, por qué no aplica una saga](../modos_fallo_s11.md#por-qué-no-aplica-una-saga)). |
| Latencia | ¿Cuánto se suma al camino de S3? | p95 medido del modelo: 1 618,8 ms ([resultado_s1_s3.json](../evaluacion_ia/resultado_s1_s3.json)), frente al objetivo de 7 000 ms. |
| Costo y operación | ¿Cuántos despliegues, configuraciones y contratos hay que mantener? | Un contenedor y un pipeline ([arc42 §7](../arc42/07-vista-de-despliegue.md)). Precio de referencia de un entorno real: 39,42 USD/mes por la máquina que aloja la API ([costo_mensual.md, §2](../costo_mensual.md)). |
| Equipo | ¿Hay responsables distintos para cada módulo? | Un equipo de cuatro personas que mantiene todos los módulos ([ADR-0001](0001-estilo-arquitectonico.md)). |

## Opciones consideradas

### Opción A — No extraer: mantener el monolito modular

- **Carga:** un solo proceso atiende con holgura el volumen supuesto.
- **Aislamiento de fallos:** ya se obtiene dentro del proceso, con el adaptador de Gemini como capa
  anticorrupción y el mensaje fijo ante fallo (ADR-0007).
- **Consistencia:** las escrituras siguen siendo locales. La única carrera detectada, la
  confirmación repetida, se resuelve con un reclamo atómico en la misma base
  ([modos_fallo_s11.md](../modos_fallo_s11.md#confirmación-de-una-acción-pendiente)).
- **Latencia:** sin cambios.
- **Costo y operación:** un despliegue, una configuración y un contrato público
  ([ADR-0002](0002-estrategia-integracion-api-sincrona.md)).
- **En contra:** un fallo del proceso (memoria agotada, excepción no controlada al arrancar) afecta a
  todos los módulos a la vez; y la disciplina de fronteras depende de las pruebas, no del despliegue.

### Opción B — Extraer `ai` a un servicio

Es el candidato natural: depende de un proveedor externo, tiene una latencia distinta del resto y su
costo crece con cada mensaje.

- **Carga:** escalar `ai` no da más capacidad, porque el límite está en la cuota de Gemini por
  minuto, no en la CPU de TAIA.
- **Aislamiento de fallos:** aislaría los fallos de proceso del módulo, pero no el fallo dominante,
  que seguiría produciendo el mismo mensaje al estudiante.
- **Consistencia:** confirmar y crear la tarea pasaría a ser una llamada por red de `ai` a
  `academic`. Si la tarea se crea y la respuesta se pierde, `ai` no sabe si reintentar. Haría falta
  una clave de idempotencia en la creación de tareas, una saga o un outbox.
- **Latencia:** suma un salto de red a cada mensaje, en el camino de S3, además de la consulta de
  tareas que hoy es una llamada en memoria.
- **Costo y operación:** dos despliegues, dos configuraciones, un contrato HTTP interno que
  versionar y la validación del JWT en los dos servicios.

### Opción C — Extraer `reminders` a un servicio

Sería el candidato si el envío programado de notificaciones (`RF-NOT-02`) necesitara correr aparte.

- **Carga:** `RF-NOT-02` sigue pendiente; hoy no hay proceso programado ni carga que aislar.
- **Consistencia:** `reminders` valida la tarea con `AcademicTaskLookup`. Por red, un recordatorio
  podría quedar apuntando a una tarea borrada entre la validación y la escritura.
- **Costo y operación:** los mismos de la opción B, sin una ganancia que los compense.

`usuario` no se considera candidato: todos los módulos dependen de `IdentityService`, de modo que
extraerlo pondría una llamada por red en el camino de casi todas las peticiones.

## Decisión

Se adopta la **opción A**: TAIA se mantiene como un monolito modular y no se extrae ningún módulo.

Ninguno de los criterios justifica hoy la extracción: no hay carga que escalar, el fallo dominante
no se resuelve separando procesos, y extraer `ai` o `reminders` crearía problemas de consistencia y
de latencia que el monolito no tiene. Las fronteras ya existentes (puertos publicados, sin claves
foráneas entre módulos, pruebas de frontera) se mantienen para que la extracción siga siendo
posible si cambian las condiciones.

### Disparadores para revisar la decisión

La decisión se revisa con un nuevo ADR si se cumple alguno de estos hechos:

1. `GET /metrics` muestra que la latencia del resto de la API se degrada por la carga de
   `POST /ai/message`.
2. Se agrega un segundo proveedor de LLM con su propio ciclo de despliegue (ADR-0007, opción C).
3. El proceso programado de `RF-NOT-02` necesita correr separado de la API. La primera respuesta
   sería un proceso trabajador con el mismo código y la misma base de datos, no un servicio nuevo.

## Consecuencias

### Positivas

- No aparecen transacciones repartidas: no hace falta saga, outbox ni claves de idempotencia entre
  servicios.
- El camino de S3 no suma llamadas de red.
- Un solo despliegue, una configuración y un contrato que mantener.
- La decisión deja escritos los hechos que la cambiarían, en lugar de dejarla abierta.

### Negativas

- Un fallo del proceso afecta a todos los módulos a la vez.
- Los módulos no se pueden escalar ni desplegar por separado.
- Las fronteras dependen de las pruebas de frontera y de la revisión: el despliegue no las impone.

## Trazabilidad

- **Requisitos:** `RNF-09` (una caída de Gemini o Telegram no impide el resto), `RF-AGT-20`
  (degradación si el LLM no está disponible), `RF-NOT-02` (envío programado, disparador 3).
- **Aspectos:** A-03, A-04 y A-05 de [aspectos.md](../aspectos.md).
- **C4:** [C4-C2](../c4/C4-C2.md), con la API como un único contenedor.
- **Análisis de soporte:** [modos_fallo_s11.md](../modos_fallo_s11.md).
- **Pruebas de frontera:** [`test_s8_closure.py`](../../backend/tests/test_s8_closure.py).
- **Implementación:** no requiere cambios de código; el commit que introduce este ADR es su registro.
