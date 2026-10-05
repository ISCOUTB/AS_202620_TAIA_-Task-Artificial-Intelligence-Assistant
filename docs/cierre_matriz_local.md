# Cierre local verificable de la matriz

Fecha: 2026-10-04. Rama inspeccionada: main.
Base: `a3e56798499ba1191156a8677a4d4c4cc067a681`.
Los cambios están en el árbol de trabajo; no se creó ningún commit.

## Correcciones implementadas

- **E-02:** `main.py` compone los casos de uso de
  `academic/adapters/inbound/structure_api.py` y
  `reminders/adapters/inbound/http_controller.py`. El endpoint de notificación
  también usa el caso de lectura inyectado para comprobar propiedad.
- **E-05:** `AcademicTaskQuery` publica filtros sin enums de dominio.
  `AcademicTaskManagementService` traduce los estados; el gateway de AI ya no
  importa el dominio ni el puerto de persistencia de Academic.
- **E-06:** `/health` ejecuta `SELECT 1` mediante
  `shared/adapters/inbound/readiness.py`. Si el driver falla, responde 503 sin
  detalles internos. Esto comprueba PostgreSQL, no disponibilidad de Gemini o
  entrega por Telegram. Se probó con conexión simulada exitosa y fallida.
- **Evaluación:** `tools/eval_llm.py` compara todos los campos etiquetados,
  incluso cuando acierta la intención; excluye el mensaje vacío antes de llamar
  al modelo; cuenta intentos fallidos; registra procedencia y hashes; cierra el
  cliente; evita copiar mensajes de excepción que podrían contener secretos.
  Los precios omitidos producen costo desconocido, no cero. Rechaza sobrescribir
  un artefacto existente. Una corrida con errores del proveedor termina con
  salida 1; la salida 0 indica ejecución sin esos errores, no aprobación de S1/S3.
- **Credenciales/CI:** se retiraron una contraseña de ejemplo de Dokploy y dos
  valores de pruebas de CI. El escáner incluye archivos nuevos no ignorados,
  documentación y contrato generado, y detecta URLs PostgreSQL con contraseña.
  CI ejecuta las auditorías y ya no exige el Compose local que Git ignora.

Decisión técnica: [ADR-0006](adr/0006-fronteras-y-evaluacion-verificable.md).
Aceptado por ratificación técnica del asistente, por delegación explícita de
Deiner. No se atribuye una aprobación individual a los demás integrantes.

## Evidencia ejecutada

Se instaló el lock de desarrollo en `.venv` con autorización del usuario,
usando `--require-hashes --only-binary :all:`. No se cambiaron versiones ni se
añadieron dependencias. El usuario rechazó instalar un servidor PostgreSQL;
no se ejecutaron pruebas contra su base de aplicación.

Rojo reproducible (lee los tres archivos originales desde Git, sin checkout):

```powershell
.\.venv\Scripts\python.exe tools/demo_s8_red.py
```

Resultado observado: **3 failed, 5 deselected**, salida 1, sobre la base indicada.
Las aserciones detectan composición en ambos controladores y acceso de AI a
internos de Academic. Al añadir posteriormente más pruebas al archivo puede
cambiar el número de casos deseleccionados, no los tres fallos esperados.

Verde reproducible sin conectarse a PostgreSQL ni a Gemini:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://postgres@127.0.0.1:55439/taia_test'
$env:GEMINI_API_KEY = [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -m pytest backend/tests/test_s8_closure.py backend/tests/test_eval_llm_measurements.py backend/tests/test_readiness.py backend/tests/test_ai_create_task_confirmation.py backend/tests/test_eval_llm_dataset.py backend/tests/test_api_contract.py backend/tests/test_ai_handle_message.py backend/tests/test_ai_gemini_llm.py backend/tests/test_ai_conversation_domain.py backend/tests/test_academic_task_domain.py backend/tests/test_reminders_notifications.py -q -p no:cacheprovider
```

Resultado observado: **105 passed, 2 warnings** (avisos de deprecación de
Starlette/httpx). Ejecutar en una terminal de pruebas sin
`TEST_DATABASE_URL`: la fixture global aplica migraciones destructivas si esa
variable está definida. La URL anterior solo permite construir la aplicación;
esta selección no necesita una base escuchando allí.

Otras comprobaciones:

- `python tools/audit_boundaries.py`: **0 infracciones, 0 aceptadas, 0 regresiones**.
  [Salida actual](auditoria_fronteras.json), línea base vacía.
  Es el resultado de las reglas implementadas, no una prueba exhaustiva de
  toda posible dependencia arquitectónica.
- `python tools/eval_llm.py --dry-run`: **39 casos, 1 vacío**.
- `python tools/eval_llm.py` sin clave: **salida 2**, sin llamadas al proveedor.

## Alcance frente a la matriz

| Criterio | Evidencia y estado del trabajo local |
| --- | --- |
| Porción real con IA y commits | Correcciones de código y trazabilidad en [ia.md](ia.md). Hay commits históricos; este incremento no tiene commit por instrucción expresa. |
| Cadena navegable | [A-03 y A-05](aspectos.md) → este informe → ADR, código, pruebas y salida de auditoría. |
| ADR argumentado | ADR-0005 histórico; ADR-0006 aceptado por delegación explícita, con restricciones, alternativas y consecuencias. |
| Prueba que falla ante el defecto | Tres regresiones rojas sobre la base de Git y verdes en el árbol corregido. |
| Resultado contrastado con el umbral | **Sigue pendiente para S1/S3 completos.** El arnés ofrece métricas parciales explícitas, no aprobación del escenario. |
| Aceptado, corregido, rechazado con motivo | Entrada 015 de [ia.md](ia.md). |
| Auditoría de fronteras y propiedad | E-02/E-05 corregidos, línea base vacía y pruebas de filtrado/propiedad. Integración PostgreSQL no ejecutada. |
| Dependencias propuestas verificadas | No se proponen dependencias nuevas. Instalación del lock existente con comprobación de hashes. |
| Sin credenciales | Escáner ampliado y limpieza de ejemplos; no se reescribió historial ni se publicaron valores privados. |
| Generativo con costo y latencia | Se conserva intacta la [medición histórica](evaluacion_ia/resultado_s1_s3.json). No hay nueva ejecución real ni nuevo resultado de calidad del modelo. |

## Lo que aún requiere datos y ejecución real

**S1** exige al menos 90 % de campos identificados y registrados correctamente
en PostgreSQL sobre 100 mensajes representativos. El dataset actual contiene
39 casos orientados a intenciones, varios sin etiquetas de campos. Hace falta
un conjunto de referencia revisado, completar el recorrido de confirmación y
lectura de lo persistido y ejecutar con Gemini y PostgreSQL de pruebas.
Generar más frases o pasar un doble de prueba no demuestra ese umbral.

**S3** exige p95 ≤ 7 s desde recepción en backend hasta envío al canal.
Las llamadas aisladas al modelo y una métrica de middleware son mediciones
parciales. Se necesita instrumentar y ejecutar el recorrido real.

Los nombres oficiales se mantienen: **S2** es puntualidad de recordatorios,
**S4** es aislamiento de datos y **S5** sustitución de proveedor en máximo dos
archivos del adaptador. Los nombres históricos de claves JSON de tokens/costo
no convierten costo en S5 ni disponibilidad en S4. No se declara cumplimiento
de esos escenarios por pruebas parciales ni por la presencia de un FakeLLM.

## Actualización tras acceso a la API y logs del operador

Fecha: 2026-10-05 UTC (2026-10-04 en Colombia).

- **Aislamiento HTTP medido:** [artefacto de ejecución](evaluacion_ia/aislamiento_c9dae4fb4f.json),
  generado por [el arnés](../tools/eval_deployed_isolation.py): 100/100 accesos
  correctos sobre 25 tareas. Se rechazaron 50/50 lecturas o ediciones ajenas
  (100 %, umbral 100 %); los 50 accesos propios tuvieron éxito. Se comprobó que
  las ediciones rechazadas no alteraron los registros. No incluye consultas
  conversacionales: `cumple_escenario_con_llm` permanece sin evaluar.
- **Limpieza:** las 25 tareas sintéticas recibieron DELETE 204 (borrado lógico).
  Permanecen dos cuentas sintéticas y la materia de prueba; no se tocaron
  cuentas ni tareas de usuarios reales. La API no permite borrar cuentas.
- **Bloqueo del generativo:** `/ai/message` devolvió 500. Los logs del operador
  identificaron JSON null frente a SQL NULL. [Diagnóstico, corrección y prueba
  roja/verde](evaluacion_ia/diagnostico_conversations_null.md).
- **Corrección local:** `JSONB(none_as_null=True)`, sin quitar la restricción,
  sin nuevas dependencias ni migración. Dos pruebas del binding real del driver
  pasan sin conectarse a una base. El despliegue de este cambio sigue pendiente.
- **Verificación conjunta:** la selección sin base de datos indicada arriba,
  añadiendo `backend/tests/test_conversation_null_binding.py`, produjo
  **107 passed, 2 warnings**. La mutación reproducible produjo **1 failed,
  1 passed** por el defecto esperado. El escáner de credenciales devolvió
  **0 hallazgos** (incluidos archivos nuevos y docs); la auditoría de fronteras,
  **0 infracciones y 0 regresiones**. Son comprobaciones de las reglas del
  escáner, no garantía absoluta de ausencia de secretos. `git diff --check`
  no encontró errores de espacios.
- **S1/S3:** no se declara cumplimiento. Se necesita desplegar la corrección,
  verificar el proveedor y completar el conjunto y recorrido descritos arriba.
  No se cambiaron resultados históricos ni se inventaron mediciones del modelo.
