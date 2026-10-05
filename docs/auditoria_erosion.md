# Auditoría de erosión de contexto y propiedad de datos — S8

## Actualización local 2026-10-04

E-02 y E-05 están corregidos en el árbol de trabajo: la composición de estructura
académica y recordatorios pasa a `main.py`; AI usa `AcademicTaskQuery` y
Academic traduce los estados. La línea base ahora está vacía y el auditor
reporta 0 infracciones. E-06 incorpora una comprobación de PostgreSQL en
`/health`, verificada con un driver simulado; no comprueba proveedores externos.

[Correcciones, pruebas rojas/verdes y limitaciones](cierre_matriz_local.md).
Las secciones siguientes conservan el diagnóstico histórico de S8; sus estados
“abierta” y “parcial” describen la situación anterior a este incremento.

Esta auditoría complementa [`auditoria_violaciones_s6.md`](auditoria_violaciones_s6.md).
Aquel documento cerró V-01 a V-04 sobre la lectura del código. Este comprueba
que ese cierre **sigue siendo cierto** y que la composición de dependencias no
se ha erosionado desde entonces. Es reproducible:

```bash
python tools/audit_boundaries.py
```

El auditor analiza el árbol con `ast`, sin red y sin base de datos, y escribe
[`auditoria_fronteras.json`](auditoria_fronteras.json). Las infracciones
registradas en [`auditoria_fronteras_baseline.json`](auditoria_fronteras_baseline.json)
se consideran analizadas y aceptadas: el comando sale con código cero mientras
no aparezca ninguna nueva.

## La evidencia de cierre de S6 no era reproducible

[`auditoria_violaciones_s6.md:48`](auditoria_violaciones_s6.md) afirma:

> no encontró imports desde `AI` hacia `academic.domain.entities.task`

El árbol actual sí lo contiene:

```python
# backend/app/modules/ai/adapters/outbound/academic_gateway.py:19
from app.modules.academic.domain.entities.task import TaskStatus
```

La misma nota, en su línea 37, describe V-03 como corregida porque
`AcademicGatewayAdapter` trabaja "sin importar repositorio ni entidad `Task`".
La primera parte es cierta —no importa `Task`, el repositorio, ni
`AcademicTaskData` desde el dominio—, pero importa `TaskStatus`, que **es** una
entidad del dominio de Academic. La corrección de V-03 fue parcial y su evidencia
de cierre no se puede reproducir sobre el código vigente. Queda abierta como
**E-05**.

La misma afirmación se repite en
[`arc42/08-conceptos-transversales.md:118`](arc42/08-conceptos-transversales.md),
que atribuye a `main.py` una concentración de la composición que solo era cierta
para dos de los cuatro contextos (E-02). Ninguna de las dos notas fue
retroalimentada por una comprobación automática; por eso este auditor existe.

## Hallazgos

### E-01 — Fuga de clientes HTTP: uno por petición, nunca cerrados

**Corregida.**

`backend/app/modules/ai/adapters/inbound/api.py` construía el modelo de lenguaje
dentro de la dependencia de FastAPI:

```python
def get_ai_use_case() -> HandleUserMessageUseCase:
    llm = GeminiLLM.from_env()      # se ejecutaba en cada petición
```

`GeminiLLM.__init__` hace `client or httpx.Client(timeout=timeout)`, y
`close()` —que existe en `gemini_llm.py:105`— no lo invoca ninguna parte de
`backend/app`. El resultado era un `httpx.Client` nuevo por petición, con su
socket y su pool, sin liberar nunca.

Dos consecuencias, y la segunda es la que más pesa:

- **Agotamiento de descriptores de archivo** bajo carga sostenida.
- **Latencia peor por diseño.** Al no reutilizarse el cliente, cada llamada al
  modelo paga un apretón de manos TCP y TLS completo contra
  `generativelanguage.googleapis.com`. S3 mide p95 de latencia de extremo a
  extremo, así que este defecto améliorable se acumulaba justo en la métrica que
  no se había podido medir todavía.

La composición se movió a `backend/app/main.py`, que es el composition root, y
el cliente se cierra con el evento `lifespan` de apagado. Ahora hay un único
cliente para toda la vida del proceso y su pool se reutiliza.

### E-02 — La composición se ha ido del composition root

**Parcialmente corregida.**

V-04 declaró que "la composición de dependencias concretas queda concentrada en
`backend/app/main.py`". Eso era cierto para Usuario y Academic, que usan
`configure_identity_service`, `configure_academic_task_lookup` y
`configure_academic_task_management`. No lo era para los otros dos contextos:

| Contexto | ¿Compone en `main.py`? | Evidencia |
| --- | --- | --- |
| Usuario | Sí | `configure_identity_service` |
| Academic | Parcial | Lookup y gestión de tareas sí; `structure_api.py:43` arma sus propios repositorios |
| AI | **No** | `api.py` construía store, gateway y LLM (corregido en S8) |
| Reminders | **No** | `http_controller.py:49-68` compone sus ocho casos de uso |

Reminders y `structure_api` de Academic siguen en la línea base como
**R1**. No se corrigieron en S8 porque hacerlo mueve la construcción de veinte
dependencias entre archivos y su propio ciclo de pruebas; se deja como
refactor planificado, con el auditor marcando la regresión si empeora.

La diferencia con V-02 no es cosmética: desde el transporte no se puede sustituir
una implementación sin tocar el adaptador HTTP, y el caso de uso deja de poder
inyectarse en las pruebas por `dependency_overrides`.

### E-03 — Singletons construidos al importar el módulo

**Corregida.**

```python
# backend/app/modules/ai/adapters/inbound/api.py:17-18 (antes)
_conversations = SqlAlchemyConversationStore(get_session_factory())
_academic = AcademicGatewayAdapter()
```

Se construían al importar, y como `main.py` importa los routers, esa
construcción ocurría durante la importación de la aplicación. Dos efectos:

- `database.py:17` llama `load_dotenv()` al importarse, así que `DATABASE_URL`
  quedaba resuelto en tiempo de importación.
- Dos colaboradores del mismo caso de uso tenían **vidas distintas**: store y
  gateway compartidos entre peticiones, LLM por petición. La mezcla hacía que el
  tiempo de vida de un caso de uso fuera indecible.

Los dos son sin estado —`SqlAlchemyConversationStore` abre una sesión por
operación y `AcademicGatewayAdapter` solo guarda el puerto—, así que compartir
un único caso de uso entre peticiones es seguro.

### E-04 — Fallo por petición en vez de fallo al arrancar

**Corregida para AI.**

`get_ai_use_case()` convertía la ausencia de `GEMINI_API_KEY` en un
`HTTP 503` **en cada petición**. El servicio arrancaba, `GET /health` respondía
`{"status": "ok"}` y el despliegue pasaba la comprobación de CD mientras todas
las peticiones reales fallaban. El síntoma que se observa en producción es
"la IA no funciona", no "el servicio está mal configurado".

Con la composición en `main.py`, la falta de la clave detiene el arranque. Es un
cambio de comportamiento deliberado: es preferible no levantar un servicio
inservible.

Efecto secundario que hubo que aceptar: `app.main` ahora necesita
`GEMINI_API_KEY` para importarse, así que la suite de pruebas la necesita. En CI
se define `una GEMINI_API_KEY de prueba no secreta`. No es una credencial:
ninguna prueba sale a la red, porque el LLM se sustituye por `FakeLLM` o por
`httpx.MockTransport`.

Queda una limitación que **no** se corrigió: `GET /health` sigue siendo superficial
para el resto del sistema. No comprueba la base de datos ni los recordatorios, y
`/mockup` responde `CD pipeline test successful` sin tocar nada. Eso excede el
alcance de esta auditoría y queda anotado en E-06.

### E-05 — V-03 no estaba del todo cerrada

**Abierta.**

`TaskStatus` es un `str, Enum` con valores `"pending"`, `"completed"` y
`"overdue"`. AI lo usa para traducir las palabras libres que produce el modelo:

```python
_STATUS_ALIASES = {
    "done": TaskStatus.COMPLETED,
    "pending": TaskStatus.PENDING,
    ...
}
```

Cruzar hacia `academic.domain.entities` hace que AI conozca el vocabulario
interno de Academic. Si Academic añadiera un estado o renombrara el valor, AI
seguiría compilando y fallaría en tiempo de ejecución, o peor, filtraría estados
que Academic ya no reconoce.

La corrección no es trivial y por eso no se aplica aquí.
`TaskQuery.status` está tipado `TaskStatus | None`, así que no basta con pasar el
string equivalente: hay que cambiar el contrato público de Academic. La opción
recomendada es que el puerto de Academic exponga la traducción del texto libre
al estado canónico —algo tipo `resolve_status(text: str) -> str | None`— de modo
que sea Academic, y no AI, quien posea el vocabulario. Eso exige tocar el
servicio de gestión, el repositorio y sus pruebas, con su propio ciclo
rojo-verde.

### E-06 — `/health` no refleja el estado real

**Anotada, fuera de alcance.**

`GET /health` es un literal. Con E-04 corregido ya no puede mentir sobre la IA,
pero sigue sin detectar una base de datos inaccesible. Merece un
`SELECT 1` y el estado de los adaptadores de salida.

## Reglas del auditor

| Regla | Qué detecta |
| --- | --- |
| **R1** | El adaptador de entrada invoca un proveedor de persistencia propio (`get_*_repository`, `get_*_provider`, `get_*_sender`) |
| **R2** | El adaptador de entrada importa la persistencia concreta de su propio contexto |
| **R3** | El adaptador de entrada lee el entorno o construye un adaptador con `.from_env()` |
| **R4** | El adaptador de entrada construye un colaborador al importarse, salvo objetos de ruta de FastAPI |
| **V-01** | Un contexto importa el adaptador HTTP de Usuario |
| **V-02** | AI o Reminders alcanzan el proveedor de repositorios de Academic |
| **V-03** | AI importa el dominio de Academic |

Las reglas R1 a R4 son stricter de lo que era la práctica del repositorio, y por
eso usan línea base: sin ella, el primer resultado habría sido ruidoso. R4 excluye
`HTTPBearer`, `APIRouter` y similares, que viven a nivel de módulo sin ser
dependencias.

## Estado

| Hallazgo | Estado |
| --- | --- |
| E-01 Fuga de clientes HTTP | Corregida |
| E-02 Composición fuera del composition root | Parcial: AI corregida; Reminders y `structure_api` en línea base |
| E-03 Singletons al importar | Corregida |
| E-04 Fallo por petición en vez de al arrancar | Corregida para AI |
| E-05 V-03 parcialmente cerrada | **Abierta**, requiere cambio de contrato en Academic |
| E-06 `/health` superficial | Anotada, fuera de alcance |

`python tools/audit_boundaries.py` sale con código cero: las tres infracciones
restantes están registradas y aceptadas, y cualquier hallazgo nuevo rompe el
comando.
