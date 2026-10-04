# Extracto de trazabilidad de IA — S8

Resumen ejecutivo de las entradas [011](ia.md), [012](ia.md),
[013](ia.md) y [014](ia.md) de [`docs/ia.md`](ia.md). El detalle completo, con las
decisiones rechazadas y el razonamiento, está en esas entradas; este documento
solo recoge lo que un lector necesita para valorar el trabajo sin leerlas enteras.

## Qué pidió el estudiante y qué se hizo

Cuatro encargos encadenados, todos sobre la entrega S8 y todos ejecutados sobre la
rama `Mark`:

1. **Encontrar y corregir un defecto real** en la confirmación de escrituras por
   lenguaje natural, con una prueba escrita antes del arreglo.
2. **Verificar dependencias y credenciales**, y reauditar si las fronteras de
   contexto que S6 declaró cerradas seguían cerradas.
3. **Eliminar credenciales por defecto** del arranque local y cerrar la
   trazabilidad de la entrega.
4. **Medir el componente generativo**: configurar `GEMINI_API_KEY`, cambiar de
   modelo cuando el configurado dejó de responder, y ejecutar la evaluación de
   S1, S3 y S5.

## Decisiones que el estudiante aceptó

| Decisión | Alternativa descartada | Motivo |
| --- | --- | --- |
| **Opción A**: normalizar con `unicodedata` + `casefold()` + quitar signos | Enumerar variantes acentuadas en `_YES` | Una lista de ortografía no termina nunca: "SÍ", "¡Sí!", "sí…" |
| **Opción A** | Preguntar al modelo si la respuesta es afirmativa | La última barrera antes de escribir no puede depender de un componente no determinista |
| Actualizar `python-dotenv` a 1.2.4 | Solo documentar la CVE | Es un parche dentro de la misma versión mayor y menor, y `load_dotenv()` se verificó idéntico |
| Mover la composición de IA a `main.py` | Dejarla en el adaptador HTTP | El patrón ya existía en Usuario y Academic; era inconsistencia, no decisión |
| Fallar al arrancar si falta la clave | Seguir devolviendo 503 por petición | Con 503, `/health` dice `ok` y un despliegue roto pasa la comprobación de CD |
| Línea base para el auditor de fronteras | Corregir las veinte infracciones de una vez | Sin triar, el primer resultado del auditor es ruido y no se usa |
| **Cambiar el modelo a `gemini-3.5-flash-lite`**, también en el código | Dejar `gemini-2.5-flash` como valor por defecto | Devolvía 404; un clon sin `GEMINI_MODEL` habría nacido roto |
| **Pausar seis segundos entre llamadas** en el arnés | Reintentar en bucle o bajar el número de casos | Los errores eran consecutivos, no aleatorios: el ritmo era la variable, no el modelo |
| **Declarar los precios con fuente y fecha** | Fijarlos en el código | Una tabla desactualizada daría un costo falsamente preciso |

## Decisiones que se rechazaron

Estas son las que más dicen sobre el rigor del trabajo:

* **Dar por buena la primera medición, de 64,1 %.** La IA exportó los diez errores
  `LLMError` como ruido. No lo eran: nueve eran consecutivos en el orden del
  dataset. Un diagnóstico con pausa, aplicado a siete de esos casos, respondió
  **7 de 7** correctamente. Se descartó la cifra y se corrigió el arnés para que
  el próximo fallo fuera diagnosticable, en vez de aceptar un 64,1 % que medía
  la velocidad de la máquina y no la capacidad del modelo. La medición válida
  posterior fue **82,05 %**.

* **Usar la credencial de producción de Supabase** que el estudiante proporcionó
  para las pruebas de integración. `backend/tests/conftest.py` ejecuta
  `alembic downgrade base` y `TRUNCATE` al iniciar la sesión: apuntar
  `TEST_DATABASE_URL` ahí habría destruido los datos de producción. Se sustituyó
  por un cluster PostgreSQL local desechable con autenticación `trust` y puerto
  propio. La credencial se eliminó del `.env`, se verificó que no está en ningún
  commit con `git log --all -S`, y **la contraseña fue rotada** por el estudiante
  en el panel del proveedor.

* **Confiar en el prefijo de la clave.** La IA afirmó que las claves de Gemini
  empiezan por `AIza`; la del estudiante no. No se validó el formato por reglas
  sino con una llamada real, que es la única forma de no discutir con una
  suposición.

* **Regenerar los lock files con la herramienta original en Linux.** Habría
  vuelto a omitir las dependencias de Windows, que es exactamente el defecto que
  se quería cerrar. Las entradas se añadieron a mano, con marcador
  `sys_platform == "win32"` y hash verificado contra PyPI.

* **Escribir un segundo adaptador de otro proveedor.** Cerraría S5 y es trabajo
  de código y pruebas; quedó fuera de alcance en vez de plantearse a medias.

* **Meter precios de tokens en el código.** El arnés los recibe por parámetro.
  Una tabla desactualizada daría un costo falsamente preciso, que es peor que no
  dar costo.

* **Corregir E-05 subiendo solo el `python-dotenv`.** `TaskQuery.status` está
  tipado con el enum del dominio, así que arreglar el import exige cambiar el
  contrato público de Academic. Queda abierto con la solución recomendada, en
  lugar de un parche a medias.

## Correcciones de las que la IA se equivocó y hubo que revertir

Se registran porque son parte del resultado:

* En `run.bat` se usó `findstr /V` para detectar la clave vacía. La lógica está
  invertida: `findstr /V /C:"GEMINI_API_KEY="` excluye **también** las líneas con
  valor. Se probó con cuatro casos y se detectó antes de commitear.
* La primera versión correcta usaba `findstr /B`, que **no funciona**: exige que
  la coincidencia empiece en la posición 0, y un `.env` en UTF-8 con BOM —lo que
  produce `Set-Content -Encoding utf8` de PowerShell 5.1— empieza con
  `EF BB BF`. Con `/B` el arranque se rechazaba siempre. Se comprobó leyendo los
  tres primeros bytes del archivo.
* El diagnóstico del primer fallo apuntaba a la clave o a la red. Era un **espacio
  inicial** en el valor de `backend/.env`, que `httpx` rechaza como cabecera
  (`Illegal header value`). Se quitó el espacio del archivo. El código sigue sin
  `.strip()`, así que el modo de fallo permanece abierto.
* Se dieron por buenos los precios de `gemini-2.5-flash` como si sirvieran para el modelo
  nuevo. La IA los marcó como no válidos hasta contrastarlos con la tabla
  oficial; resultaron ser los mismos, pero por el camino se escribió de dónde
  salen y de cuándo se consultaron.
* Dos enlaces añadidos a documentos nuevos apuntaban a `../arc42/`, que desde
  `docs/` es un nivel de más. Y otro apuntaba a
  `arc42/04-estrategia-de-calidad.md`, archivo que no existe: el real es
  `04-estrategia-de-solucion.md`.
* El primer auditor de fronteras marcaba `main.py`, que **es** el composition
  root y sí puede componer, y marcaba `HTTPBearer()` como una dependencia. Ambos
  falsos positivos se corrigieron antes de sacar conclusiones.
* Una prueba de integridad del dataset exigía que `json.loads` **lanzara**
  `ValueError` en cada línea, cuando lo que se quería era lo contrario. Falló y
  se invirtió.

## Estado al cierre

| Ítem | Estado |
| --- | --- |
| Defecto D-S8-01 | Corregido, con evidencia roja y verde |
| Dependencias y credenciales | Verificado, 0 problemas |
| Fronteras de contexto | Auditoría hecha; 3 hallazgos corregidos, 1 abierto |
| Credenciales de desarrollo | Eliminado el secreto por defecto |
| Credenciales expuestas | **Rotadas**: la de Supabase y la clave de Gemini |
| S2 (confirmación) | **Medido**: 364/364 y 0 escrituras indebidas |
| S1 (intención) | **Medido**: 82,05 %, 32 de 39, sin errores |
| S3 (latencia del modelo) | **Medido**: p95 1 618,8 ms sobre 39 muestras |
| S5 (costo) | **Medido**: 0,000312 USD por operación |
| S4 (disponibilidad) | **Pendiente**: exige despliegue y observación en el tiempo |
| Suite completa | 202 pruebas en verde |

## Advertencia

Las dos credenciales que se compartieron en el canal de conversación —la
contraseña de producción de Supabase y la clave de Gemini— **ya fueron
rotadas**. Ninguna de las dos llegó a un commit: `git log --all -S` sobre el
patrón del *pooler* de Supabase y sobre el prefijo de la clave de Gemini no
devuelve coincidencias, y `git grep` sobre el árbol versionado devuelve 0
hallazgos. Aun así, conviene recordar por qué importa comprobarlo: una
credencial expuesta fuera del control de versiones no se arregla limpiando el
repositorio, se arregla rotándola.