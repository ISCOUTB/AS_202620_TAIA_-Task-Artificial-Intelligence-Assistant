# Bitácora S8 — paso a paso

Esta bitácora cuenta, en orden, qué se hizo en la semana 8: qué se encontró, qué se
cambió y **dónde está la prueba de cada cosa**. Está pensada para que alguien que no
estuvo en la conversación pueda seguir el rastro sin tener que confiar en la palabra de
nadie: cada afirmación importante apunta a un archivo o a una corrida pública de
integración continua.

Si solo te interesa una sección, ve directo al [mapa de evidencias](#1-mapa-de-evidencias-léelo-primero).

---

## 1. Mapa de evidencias (léelo primero)

| Qué se demuestra | Dónde está la evidencia | Commit | Resultado |
| --- | --- | --- | --- |
| El proyecto partía de una base sana | [`evidencia_s8_baseline.txt`](evidencia_s8_baseline.txt) | `4b07242` | `171 passed`, salida 0 |
| **El defecto D-S8-01 existía de verdad** | [`evidencia_s8_pre-fix.txt`](evidencia_s8_pre-fix.txt) + [corrida roja][run-rojo] | `74a5126` | `7 failed, 180 passed`, salida 1 |
| **El arreglo lo corrigió** | [`evidencia_s8_post-fix.txt`](evidencia_s8_post-fix.txt) + [corrida verde][run-verde-fix] | `9160c4b` | `202 passed`, salida 0 |
| La confirmación es correcta y es instantánea | [`evaluacion_confirmacion.json`](evaluacion_confirmacion.json) | — | 364/364 aceptadas, 0/20 escrituras indebidas, p95 `0.0338 ms` |
| Las dependencias están íntegras y no hay credenciales | [`verificacion_dependencias_s8.md`](verificacion_dependencias_s8.md) + [`verificacion_dependencias.json`](verificacion_dependencias.json) | — | 24 + 31 paquetes, 0 sin hash, 0 credenciales |
| Los límites del módulo siguen donde deben | [`auditoria_fronteras.json`](auditoria_fronteras.json) + [`auditoria_fronteras_baseline.json`](auditoria_fronteras_baseline.json) | — | auditor en exit 0, 3 hallazgos en línea base |
| El defecto de S6 sí existía | [`auditoria_erosion.md`](auditoria_erosion.md) | — | 6 hallazgos: E-01 a E-06 |
| El modelo tiene casos etiquetados | [`evaluacion_ia/dataset.jsonl`](evaluacion_ia/dataset.jsonl) | — | 39 casos, 5 intenciones |
| **Y ya se midió contra el modelo real** | [`evaluacion_ia/resultado_s1_s3.json`](evaluacion_ia/resultado_s1_s3.json) | — | S1 82,05 %, S3 p95 1 618,8 ms, S5 0,000312 USD/op, 0 errores |
| La entrega está completa y auditable | [`entrega_s8.md`](entrega_s8.md) | `fa8fe6e` | índice maestro |
| La trazabilidad de IA de la semana | [`ia.md`](ia.md) entradas 011-014 | — | qué se aceptó y qué se rechazó |

---

## 2. El defecto que originó todo: D-S8-01

### Qué pasaba

Para crear una tarea, el asistente pregunta si se confirma. La respuesta se comparaba
contra una lista de palabras aceptadas. El problema no estaba en la lista, sino en **cómo
se comparaba**:

```python
# antes
if texto.lower() in _YES:
```

`.lower()` convierte "Sí" en "sí", **con tilde**. Y la lista contenía `"si"`, **sin
tilde**. Es decir: la palabra que la gente escribe de manera natural nunca coincidía con
la que el código buscaba.

**Consecuencia:** la tarea no se creaba y no pasaba nada. Ni error, ni aviso. El usuario
creía que la tarea estaba guardada y simplemente se perdía. Un fallo silencioso es peor
que uno visible, porque nadie lo reporta.

### Cómo se comprobó

Escribimos primero la prueba que **falla**, y solo después tocamos el código. La
prueba vive en [`backend/tests/test_ai_create_task_confirmation.py`](../backend/tests/test_ai_create_task_confirmation.py)
y contiene 16 casos. Siete de ellos son exactamente las variantes acentuadas:

```
test_confirmacion_crea_la_tarea[acentuada-minuscula]
test_confirmacion_crea_la_tarea[acentuada-capitalizada]
test_confirmacion_crea_la_tarea[acentuida-mayuscula]
test_confirmacion_crea_la_tarea[acentuada-con-punto]
test_confirmacion_crea_la_tarea[acentuada-con-espacios]
test_confirmacion_crea_la_tarea[acentuada-con-exclamacion]
test_confirmacion_crea_la_tarea[acentuada-con-exclamaciones]
```

(El identificador `acentuida-mayuscula` está así en el código, con la `i` cambiada. Se
deja tal cual porque es el nombre real del caso y conviene poder buscarlo tal cual
aparece.)

### Por qué el orden importa

Si hubiéramos arreglado primero y escrito la prueba después, la prueba habría pasado a la
primera, siempre. Y una prueba que siempre pasa no demuestra nada: puede pasar porque el
código está bien, o porque la prueba no mide lo que dice medir.

Por eso existe la corrida roja publicada. Si alguien quiere comprobar que la prueba
detectaba el defecto, abre el [log de la corrida roja][run-rojo] y ve las siete pruebas
en rojo sobre el mismo commit que después quedó verde.

### El arreglo

Sustituimos la comparación frágil por normalización determinista, documentada en
[ADR-0005](adr/0005-normalizacion-confirmacion-espanol.md):

```python
def _normalizar_respuesta(texto: str) -> str:
    # quita tildes, pasa a minúsculas sin acentos, deja solo letras y espacios
```

La normalización es deliberadamente **local y determinista**, no una llamada al modelo.
La razón está desarrollada en [Una decisión que conviene conocer](entrega_s8.md#una-decisión-que-conviene-conocer):
la última barrera de escritura no puede depender de que la IA interprete bien una frase.

---

## 3. Recorrido paso a paso

### Paso 0 — Entorno y línea base

Se levantó una instancia PostgreSQL **desechable** en `localhost:5433` con las bases
`taia` y `taia_test`, y se fijó la línea base del proyecto: **171 pruebas en verde**
([`evidencia_s8_baseline.txt`](evidencia_s8_baseline.txt), commit `4b07242`).

Importante: la base `taia_test` se **destruye y se reconstruye en cada corrida**
(`backend/tests/conftest.py` ejecuta `alembic downgrade base` y `TRUNCATE`). Jamás se
apuntó a la base de producción. Cualquier cifra de esta bitácora viene de esa base
desechable.

### Paso 1 — Supply chain y CI

`python-dotenv` 1.1.1 tenía una vulnerabilidad conocida (**CVE-2026-28684**,
PYSEC-2026-2270, GHSA-mf9w-mj56-hr94). Se actualizó a **1.2.4**.

Se añadieron además `tzdata==2026.5` y `colorama==0.4.6`, porque en Windows las zonas
horarias y los colores no vienen del sistema y sin ellos la instalación no era
reproducible. Y se fijó la imagen base de la imagen de Docker **por digest**:

```
uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21
```

Commit `66c1d83`. Ese commit también arregló tres errores de `test_usuario_auth_me.py`
y dejó la CI ejecutando la suite completa, que antes no lo hacía.

### Paso 2 — Prueba roja y arreglo de D-S8-01

Detalle en la [sección 2](#2-el-defecto-que-originó-todo-d-s8-01). Commits `74a5126`
(rojo) y `9160c4b` (verde).

### Paso 3 — Medición offline de la confirmación (S2)

La confirmación no usa IA: es lógica de texto. Eso permitido medirla miles de veces sin
internet y sin pagar nada. Se escribió [`tools/eval_confirmacion.py`](../tools/eval_confirmacion.py):

- **364/364** formas afirmativas aceptadas (9 palabras × 3 capitalizaciones × 14 envolturas)
- **0/20** escrituras indebidas, incluidas casi-confirmaciones como "sii" y "sí no"
- p50 `0.0142 ms`, p95 `0.0338 ms`, máximo `0.1686 ms`

Salida completa en [`evaluacion_confirmacion.json`](evaluacion_confirmacion.json).

El resultado relevante para una decisión de diseño: el p95 es de **0.03 ms**. Confirmarle
una tarea al usuario no cuesta nada en rendimiento, así que no hay razón para mover esa
comprobación al lado asíncrono.

### Paso 4 — Auditoría de erosión

El hallazgo de fondo de esta semana **no fue un defecto de código, sino de proceso**: la
evidencia de cierre de S6 afirmaba cosas que **no se podían reproducir**. Por ejemplo,
decía que no existía ningún import de IA hacia el dominio de Academic, y sí existía.

Nada de eso era mentira deliberada: simplemente nadie lo volvió a comprobar. La respuesta
fue construir [`tools/audit_boundaries.py`](../tools/audit_boundaries.py), que verifica
esas afirmaciones automáticamente, y registrar seis hallazgos. Están explicados en
[`auditoria_erosion.md`](auditoria_erosion.md).

| Hallazgo | Qué era | Estado |
| --- | --- | --- |
| E-01 | `httpx.Client` creado por petición y nunca cerrado | **Corregido** |
| E-02 | Login desalineado en la línea base | Parcial, anotado |
| E-03 | Atajo local en `ai/services.py` | **Corregido** |
| E-04 | Composición de `GeminiLLM` en la capa de entrada | **Corregido** |
| E-05 | `academic_gateway.py` importa `TaskStatus` del dominio de Academic | **Abierto** |
| E-06 | Alcance de Hermes–CDP sin verificar | Anotado |

**E-01 era el más serio.** Sin reutilización del cliente, cada mensaje abría una conexión
nueva con Google y la tiraba a la basura. Eso importa por un motivo concreto: pagar un
handshake TCP+TLS por mensaje es exactamente el tipo de cosa que infla la latencia
medida. Se estaba midiendo un defecto propio como si fuera una limitación del modelo.

### Paso 5 — Composición de IA y medición de costo (S5)

Como corrección de E-03 y E-04, la creación del cliente de IA se movió al **composition
root**, [`backend/app/main.py`](../backend/app/main.py). Ahora hay un único `GeminiLLM`
por proceso, cerrado al apagar mediante `lifespan`.

Un efecto secundario valioso: **sin `GEMINI_API_KEY` la aplicación ahora se niega a
arrancar**. Antes arrancaba, el endpoint de salud reportaba `ok`, y cada mensaje devolvía
error. Es la diferencia entre un coche que dice "todo bien" sin gasolina y uno que dice
"no hay gasolina".

Para poder medir lo que cuesta la IA se añadió `LLMUsage` al puerto: tokens de entrada y
salida, `finish_reason` y si la respuesta quedó **truncada** por alcanzar el límite de
tokens. Sin ese último dato no se distingue una respuesta completa de una cortada.

**Decisión de diseño:** esa información se registra **solo en los logs del servidor**, no en
la respuesta de la API. El contrato HTTP con el frontend está congelado desde antes, y
agregar campos lo rompería. Se puede medir el costo sin tocar el contrato.

### Paso 6 — Configuración local

Dos defectos, ambos corregidos en `8282044`:

**La clave de secreto escrita en el propio programa.** `run.bat` traía
`un secreto JWT de desarrollo`, lo que contradice RNF-02. Traducido: el código de
la puerta estaba impreso en la fachada. Ahora el script exige una clave real y aborta con
código 1 si falta.

**El `.env` del desarrollador se ignoraba en silencio.** El script definía su propia
`DATABASE_URL` antes de leer el archivo, y `load_dotenv` **no sobrescribe** variables ya
definidas. El archivo personal nunca se aplicaba y el programa arrancaba apuntando a otra
base sin avisar. Es como un formulario que siempre conserva la respuesta marcada por
defecto e ignora lo que escribiste.

También se creó [`.env.example`](../.env.example) y se forzó a versionarlo con
`!.env.example`: la plantilla **no existía** en el repositorio porque una regla de
ignorado se la tragaba. El proyecto decía "copia la plantilla" y la plantilla no estaba.

### Paso 7 — Dataset y arnés de evaluación con IA

Se preparó lo necesario para medir lo que **sí** depende del modelo, aunque todavía no se
pueda ejecutar:

- [`docs/evaluacion_ia/dataset.jsonl`](evaluacion_ia/dataset.jsonl): **39 casos**
  etiquetados, 5 intenciones (6 create, 9 query, 5 update, 3 help, 16 unknown).
- [`tools/eval_llm.py`](../tools/eval_llm.py): matriz de confusión, latencia, tokens y
  precios por argumento, para no dejar el costo hardcodeado.

Sin `GEMINI_API_KEY`, `eval_llm.py` sale con **código 2** y declara la medición pendiente.
Preferimos un hueco honesto a una cifra inventada: un número falso en un informe es peor
que un número ausente.

### Paso 8 — Cierre, trazabilidad y limpieza del historial

- [`docs/entrega_s8.md`](entrega_s8.md): índice maestro de la entrega.
- [`docs/extracto_ia_s8.md`](extracto_ia_s8.md): resumen ejecutivo, decisiones aceptadas y
  alternativas descartadas, y los errores propios que hubo que revertir.
- [`docs/ia.md`](ia.md) entradas 011, 012 y 013.
- Los diez mensajes de commit de S8 se acortaron a una línea sin cuerpo, para igualar el
  estilo que el repositorio ya usaba. Eso reescribió el historial, así que **todas las
  evidencias se regeneraron** y se actualizaron las referencias (commit `97b8996`).

### Paso 9 — Credenciales, cambio de modelo y la medición de S1, S3 y S5

Este paso cerró lo que los ocho anteriores dejaron como hueco explícito: **S1, S3 y S5
estaban pendientes por falta de `GEMINI_API_KEY`**.

**Las credenciales primero.** El `.env` de la raíz contenía una `DATABASE_URL` del
*pooler* de Supabase **con contraseña**. No estaba versionado —`git log --all` no lo
muestra nunca— pero viajaba dentro del archivo comprimido del proyecto. Se eliminó, y
la contraseña **fue rotada** por el estudiante en el panel del proveedor. La clave de
Gemini quedó expuesta en la conversación, en un mensaje y en un *traceback*: se
eliminó en AI Studio y se creó otra, que es la que vive hoy en `backend/.env`.
`.env.example` quedó con `GEMINI_API_KEY=` vacío. Los detalles están en
[`verificacion_dependencias_s8.md`](verificacion_dependencias_s8.md).

**El primer fallo no era de la clave.** `Illegal header value` apareció por primera
vez al probar la llamada. La IA señaló la clave o la red; el error real era un
**espacio inicial** en el valor de `backend/.env`, que `httpx` rechaza como
cabecera. Se quitó el espacio del archivo. El código **no** se cambió:
`gemini_llm.py:100` sigue leyendo la variable sin `.strip()`.

**El modelo por defecto ya no existía.** `gemini-2.5-flash` devolvió **404** con una
credencial nueva. Se consultó la página oficial de deprecaciones, que atribuye la
restricción de los modelos 2.5 a las cuentas que ya los usaban, y se pasó a
`gemini-3.5-flash-lite`: primero con `GEMINI_MODEL`, y después en el código, porque un
clon sin esa variable habría nacido roto. El riesgo quedó documentado en la sección 11.7
de [`arc42/11`](arc42/11-riesgos-y-deudas-tecnicas.md).

**La primera medición no valía.** `tools/eval_llm.py` dio **64,1 %** (25 de 39) con 10
errores `LLMError`. La IA los reportó como ruido. No lo eran: nueve eran
**consecutivos** en el orden del dataset (`u001` a `h004`), y un problema del modelo no
produce un bloque de nueve. Para poder distinguirlo hizo falta un dato que el arnés no
guardaba —el **mensaje** del error, no solo su tipo— y un guion de diagnóstico que
repetía siete de los casos fallidos de uno en uno, con seis segundos de pausa entre
llamadas. Los siete respondieron **7 de 7** correctamente.

**La corrección fue al arnés, no al modelo.** Se añadieron `PAUSA_ENTRE_LLAMADAS = 6` y
el mensaje completo del error. Con eso, la corrida de 39 llamadas terminó **sin un solo
error** y con **82,05 %** de exactitud: es la medición que se reporta en
[`resultado_s1_s3.json`](evaluacion_ia/resultado_s1_s3.json), con p50 1 293,3 ms, p95
1 618,8 ms y 0,000312 USD por operación.

> **Lo que este paso no resolvió.** El producto sigue sin manejar el `429`: el arnés
> sortea el límite por minuto con una pausa, la aplicación no lo sortea. Y la causa
> exacta de los errores de la primera corrida **no se confirmó** —límite por minuto o
> saturación—, porque el arnés solo guardaba el nombre del error, que es justo el dato
> que faltaba. Está anotado como deuda técnica en la sección 7.

---

## 4. Índice de evidencias

### 4.1 Archivos de texto generado

| Archivo | Qué contiene | Commit | Resultado |
| --- | --- | --- | --- |
| [`evidencia_s8_baseline.txt`](evidencia_s8_baseline.txt) | Línea base previa a cualquier cambio | `4b07242` | `171 passed`, salida 0 |
| [`evidencia_s8_pre-fix.txt`](evidencia_s8_pre-fix.txt) | **La prueba roja** | `74a5126` | `7 failed, 180 passed`, salida 1 |
| [`evidencia_s8_post-fix.txt`](evidencia_s8_post-fix.txt) | La prueba verde | `fa8fe6e` | `202 passed`, salida 0 |

Los tres los produce [`tools/evidencia_s8.py`](../tools/evidencia_s8.py), que corre la
suite completa y graba la salida tal cual, con el commit y la base de datos usados.

### 4.2 Integración continua

| Corrida | Commit | Conclusión | Qué demuestra |
| --- | --- | --- | --- |
| [Roja][run-rojo] | `74a5126` | **failure** | La prueba detecta el defecto |
| [Verde del arreglo][run-verde-fix] | `9160c4b` | **success** | El arreglo lo corrige |
| [Verde post-fix][run-verde-post] | `fa8fe6e` | **success** | La entrega completa en verde |
| [Verde HEAD][run-head] | `97b8996` | **success** | Estado final de la rama |

> **Sobre estas corridas.** Los mensajes de los commits se acortaron reescribiendo el
> historial, y un force-push genera **un único evento de push**: por eso CI no corrió
> para los commits intermedios. Para recuperar la corrida roja y la verde se publicaron
> los commits `74a5126` y `9160c4b` en dos ramas temporales, que ya se eliminaron. Son
> los mismos objetos de commit que están en `Mark`. La explicación está escrita dentro de
> las propias evidencias, no solo aquí.

### 4.3 Salidas de las herramientas

| Archivo | Generado por |
| --- | --- |
| [`evaluacion_confirmacion.json`](evaluacion_confirmacion.json) | [`tools/eval_confirmacion.py`](../tools/eval_confirmacion.py) |
| [`verificacion_dependencias.json`](verificacion_dependencias.json) | [`tools/verificar_dependencias.py`](../tools/verificar_dependencias.py) |
| [`auditoria_fronteras.json`](auditoria_fronteras.json) | [`tools/audit_boundaries.py`](../tools/audit_boundaries.py) |
| [`auditoria_fronteras_baseline.json`](auditoria_fronteras_baseline.json) | el mismo auditor, lista de excepciones aceptadas |
| [`evaluacion_ia/dataset.jsonl`](evaluacion_ia/dataset.jsonl) | a mano, 39 casos etiquetados |
| [`evaluacion_ia/resultado_s1_s3.json`](evaluacion_ia/resultado_s1_s3.json) | [`tools/eval_llm.py`](../tools/eval_llm.py), 39 llamadas a `gemini-3.5-flash-lite` |

### 4.4 Etiqueta de Git

```bash
git show s8-pre-fix
```

La etiqueta `s8-pre-fix` apunta al commit rojo `74a5126`. Es la forma más rápida de
llegar al estado con el defecto presente, sin buscarlo en el historial.

---

## 5. Cómo reproducir cada paso

Con la base de datos local levantada en `localhost:5433` y en PowerShell:

```powershell
$env:PYTHONUTF8 = '1'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://postgres@localhost:5433/taia_test'
$env:DATABASE_URL = 'postgresql+psycopg://postgres@localhost:5433/taia'
$env:GEMINI_API_KEY = '<valor-no-secreto-para-pruebas>'

# suite completa: debe dar 202 passed
python -m pytest backend/tests -q

# S2, la confirmación (sin red, sin IA)
python tools/eval_confirmacion.py

# supply chain y credenciales
python tools/verificar_dependencias.py

# límites del módulo y línea base
python tools/audit_boundaries.py

# el dataset con clave, o solo la validación sin clave
python tools/eval_llm.py --dry-run

# S1, S3 y S5: la corrida del Paso 9 (~4 min, con 6 s de pausa entre llamadas)
python tools/eval_llm.py --precio-input 0.30 --precio-output 2.50 `
  --json docs/evaluacion_ia/resultado_s1_s3.json

# regenerar las evidencias.txt
python tools/evidencia_s8.py post-fix
```

La corrida con clave necesita `GEMINI_API_KEY` en `backend/.env` y **no** debe
usar `una GEMINI_API_KEY no secreta` como la de las pruebas: el
arnés llama a la API de verdad. Los precios se pasan por argumento y hay que
volver a consultarlos; los de arriba son los declarados el 2026-10-04 para
`gemini-3.5-flash-lite`.

`PYTHONUTF8=1` hace falta en Windows porque el generador de evidencia lee la salida de
pytest con la codificación del sistema, que en Windows es `cp1252`, y el output de pytest
contiene caracteres UTF-8. Sin esa variable el generador falla con un `AttributeError`
en su línea 83. **Es un defecto conocido y pendiente de corregir, documentado en la
[sección 7](#7-deudas-técnicas-que-quedan).**

Para ver el defecto original sin tocar nada:

```bash
git show s8-pre-fix:backend/app/modules/ai/application/use_cases/handle_message.py
```

---

## 6. Lo que no se pudo hacer, y por qué

| Medición | Estado | Motivo |
| --- | --- | --- |
| S2: confirmación | **Medida** | No depende de la IA |
| S1: qué tan bien responde el modelo | **Medida** | 82,05 % (32 de 39), sin errores. Limitada a la intención, no a los campos; ver `entrega_s8.md` |
| S3: latencia | **Medida** | p95 1 618,8 ms sobre 39 muestras, **solo del tramo del modelo** |
| S5: costo por operación | **Medida** | 0,000312 USD por operación a los precios declarados |
| S4: disponibilidad real | **Pendiente** | Sin despliegue desde `main` |

`tools/eval_llm.py` **sigue** saliendo con código 2 cuando no hay `GEMINI_API_KEY`: esa
rama no se tocó y no se le dio un valor por defecto. Los precios de token tampoco están
en el código, se pasan por argumento.

### Lo que S3 no es

S3 se reporta como medida, con una salvedad que conviene no perder de vista: mide el
tramo entre la máquina del estudiante y la respuesta de Gemini. **No** incluye Telegram,
ni el gateway académico, ni la base de datos, ni el cifrado de la API. El p95 de
1,62 s es una cota optimista de lo que verá el estudiante, y por eso el escenario S3
sigue sin cerrarse del todo.

---

## 7. Deudas técnicas que quedan

**1. La aplicación no maneja el `429`.** Es la deuda que dejó el Paso 9. El nivel
gratuito de Gemini limita las llamadas por minuto; el arnés lo sortea con
`PAUSA_ENTRE_LLAMADAS = 6`, y `GeminiLLM` no reintenta ni explica. Un estudiante en el
récord de uso vería que el asistente no responde, sin motivo. Además,
`gemini_llm.py:153` registra solo `type(error).__name__`, de modo que un fallo de
transporte no deja rastro útil en el log. El riesgo está en la sección 11.6 de
[`arc42/11`](arc42/11-riesgos-y-deudas-tecnicas.md).

**2. La clave se lee sin `.strip()`.** `gemini_llm.py:100` hace
`os.getenv("GEMINI_API_KEY", "")`. Un `backend/.env` con un espacio antes del valor
—lo produce `Set-Content` de PowerShell— produce `Illegal header value` y ni el
mensaje ni el arranque dicen por qué. El arreglo es una llamada. Se documentó en vez
de aplicarse porque quedaba fuera del alcance del paso.

**3. El arnés no aplica el descarte que el dataset declara.** `dataset.jsonl:28`
(`x002`) tiene el texto vacío y la nota «vacío, se rechaza antes del modelo», pero
`tools/eval_llm.py` lo envía al modelo como cualquier otro caso. El modelo lo respondió
`unknown`, así que el caso cuenta como acierto y no baja la media. S1 se reporta como
32 de 39 y no como 32 de 38, porque 32 de 39 es lo que el arnés midió. Cerrarlo exige
implementar el filtro y volver a medir.

**4. El JSON de evaluación no es auto-descriptivo.** `resultado_s1_s3.json` registra
métricas, pero **no** qué modelo las produjo, ni la fecha, ni el commit. El modelo
(`gemini-3.5-flash-lite`), la fecha (2026-10-04) y los precios (0,30 y 2,50 USD por
millón) están declarados en `entrega_s8.md`, que es la fuente. Añadir esos campos al
arnés es trabajo futuro; no se rellenaron a mano, porque retocar un artefacto de
medición después de producido lo convierte en una cifra sin procedencia.

**5. ~~Rotar la contraseña de producción de Supabase.~~ Cerrada en el Paso 9.** Se
compartió en el canal de conversación y estuvo en `backend/.env`. Nunca estuvo en
ningún commit, y `git log --all -S` sobre el patrón del *pooler* no devuelve
coincidencias. Aun así, la exposición ocurrió fuera del control de versiones y borrar
el archivo no deshace que alguien la haya leído, así que **el estudiante la rotó en el
panel del proveedor**. Lo mismo se hizo con la clave de Gemini que apareció en la
conversación: se eliminó en AI Studio y se creó otra. Se conservan aquí las dos
entradas, y no como deudas, porque el valor de esta bitácora es también registrar qué
se cerró.

**6. E-05 abierto a propósito.** `academic_gateway.py` importa `TaskStatus` desde el
dominio de Academic. Corregirlo **rompe la interfaz pública** de `task_management.py`,
porque `TaskQuery.status` está tipado con ese enum. Exige cambiar el contrato y
reejecutar las pruebas de contrato. Se documentó la solución recomendada en vez de
aplicar un parche a medias que dejara el contrato inconsistente.

**7. `tools/evidencia_s8.py` falla en Windows.** Ya descrito en la
[sección 5](#5-cómo-reproducir-cada-paso). El arreglo es una línea: pasar `encoding="utf-8"`
al `subprocess.run` de la línea 64.

**8. `postgres:18` en `.github/workflows/ci.yml` es una etiqueta mutable.** Cambiar el
contenido de la imagen no requiere cambiar la etiqueta, así que dos corridas distintas
podrían usar imágenes distintas. Ninguna documentación de esta entrega afirma que el
supply chain esté cerrado en su totalidad. Fijar el digest es un cambio de una línea.

---

## Referencias cruzadas

- [`entrega_s8.md`](entrega_s8.md) — índice maestro y tabla de defectos
- [`extracto_ia_s8.md`](extracto_ia_s8.md) — resumen ejecutivo de la trazabilidad de IA
- [`ia.md`](ia.md) — entradas 011, 012 y 013
- [`auditoria_erosion.md`](auditoria_erosion.md) — E-01 a E-06 en detalle
- [`verificacion_dependencias_s8.md`](verificacion_dependencias_s8.md) — dependencias y CVE
- [`adr/0005-normalizacion-confirmacion-espanol.md`](adr/0005-normalizacion-confirmacion-espanol.md) — la decisión de normalizar

[run-rojo]: https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions/runs/37153176450
[run-verde-fix]: https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions/runs/37153179644
[run-verde-post]: https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions/runs/37153135794
[run-head]: https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions/runs/37153562178
