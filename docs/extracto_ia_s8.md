# Extracto de trazabilidad de IA — S8

Resumen ejecutivo de las entradas [011](ia.md), [012](ia.md) y
[013](ia.md) de [`docs/ia.md`](ia.md). El detalle completo, con las decisiones
rechazadas y el razonamiento, está en esas entradas; este documento solo
recoge lo que un lector necesita para valorar el trabajo sin leerlas enteras.

## Qué pidió el estudiante y qué se hizo

Tres encargos encadenados, todos sobre la entrega S8 y todos ejecutados sobre la
rama `Mark`:

1. **Encontrar y corregir un defecto real** en la confirmación de escrituras por
   lenguaje natural, con una prueba escrita antes del arreglo.
2. **Verificar dependencias y credenciales**, y reauditar si las fronteras de
   contexto que S6 declaró cerradas seguían cerradas.
3. **Eliminar credenciales por defecto** del arranque local y cerrar la
   trazabilidad de la entrega.

## Decisiones que el estudiante aceptó

| Decisión | Alternativa descartada | Motivo |
| --- | --- | --- |
| **Opción A**: normalizar con `unicodedata` + `casefold()` + quitar signos | Enumerar variantes acentuadas en `_YES` | Una lista deORTography no termina nunca: "SÍ", "¡Sí!", "sí…" |
| **Opción A** | Preguntar al modelo si la respuesta es afirmativa | La última barrera antes de escribir no puede depender de un componente no determinista |
| Actualizar `python-dotenv` a 1.2.4 | Solo documentar la CVE | Es un parche dentro de la misma versión mayor y menor, y `load_dotenv()` se verificó idéntico |
| Mover la composición de IA a `main.py` | Dejarla en el adaptador HTTP | El patrón ya existía en Usuario y Academic; era inconsistencia, no decisión |
| Fallar al arrancar si falta la clave | Seguir devolviendo 503 por petición | Con 503, `/health` dice `ok` y un despliegue roto pasa la comprobación de CD |
| Línea base para el auditor de fronteras | Corregir las veinte infracciones de una vez | Sin triar, el primer resultado del auditor es ruido y no se usa |

## Decisiones que se rechazaron

Estas son las que más dicen sobre el rigor del trabajo:

* **Usar la credencial de producción de Supabase** que el estudiante proporcionó
  para las pruebas de integración. `backend/tests/conftest.py` ejecuta
  `alembic downgrade base` y `TRUNCATE` al iniciar la sesión: apuntar
  `TEST_DATABASE_URL` ahí habría destruido los datos de producción. Se sustituyó
  por un cluster PostgreSQL local desechable con autenticación `trust` y puerto
  propio. La credencial se eliminó del `.env`, se verificó que no está en ningún
  commit con `git log --all -S`, y **queda pendiente que el estudiante la rote**,
  porque se expuso fuera del repositorio.

* **Regenerar los lock files con la herramienta original en Linux.** Habría
  vuelto a omitir las dependencias de Windows, que es exactamente el defecto que
  se quería cerrar. Las entradas se añadieron a mano, con marcador
  `sys_platform == "win32"` y hash verificado contra PyPI.

* **Medir S1 y S3 con Gemini sin clave.** No hay `GEMINI_API_KEY`. Se construyó
  el arnés y el dataset, y ambos valores quedaron marcados como pendientes. Un
  número estimado habría sido indistinguible de uno medido en el informe.

* **Poner precios de tokens en el código.** El harness los recibe por parámetro.
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
| S2 (confirmación) | **Medido**: 364/364 y 0 escrituras indebidas |
| S1, S3 extremo a extremo, S4, S5 | **Pendientes** por falta de `GEMINI_API_KEY` |
| Suite completa | 202 pruebas en verde |

## Advertencia

La contraseña de producción de Supabase fue compartida en el canal de
conversación y llegó a escribirse en `backend/.env`, que está en `.gitignore` y
nunca se versionó. No aparece en ningún commit, pero **debe rotarse**: la
exposición fue fuera del control de versiones, y eso no lo arregla limpiar el
repositorio.