# 7. Vista de despliegue

> Actualización operativa: el backend se despliega mediante `docker-compose.yml`
> y Dokploy, con PostgreSQL configurable, migraciones Alembic y health check.
> La [guía de despliegue vigente](../despliegue-dokploy.md) sustituye las
> instrucciones de operación del corte inicial descrito en esta vista histórica.

La arquitectura de despliegue distingue entre la **arquitectura objetivo** y el **corte vertical actualmente ejecutable**.

| | |
|---|---|
| URL pública | `http://157.137.215.57:8000` |
| Health check | `GET http://157.137.215.57:8000/health` → `200 {"status": "ok"}` |
| Métrica | `GET http://157.137.215.57:8000/metrics` |
| Documentación interactiva | `http://157.137.215.57:8000/docs` |
| Respaldo (alternativa del taller) | `https://taia-backend-latest.onrender.com` |

## 7.1. Infraestructura: una caja por pieza

```text
┌──────────────────────┐ git push ┌──────────────────────────────────────┐
│ Equipo de desarrollo │─────────►│ [2] GitHub Actions (ubuntu-latest)   │
│ [9] Terraform CLI    │          │ ci.yml: pruebas y contrato           │
│     (estado local)   │          │ cd.yml: build, push y deploy         │
└──────────┬───────────┘          └─────┬──────────────────────┬─────────┘
           │ API de OCI                 │ SSH + secretos       │ docker push
           │                            │                      ▼
           │                            │           ┌──────────────────────┐
           │                            │           │ [3] GHCR             │
           │                            │           │ taia_backend:<sha12> │
           │                            │           │ taia_backend:latest  │
           │                            │           └────┬────────────┬────┘
           │                            │    docker pull │            │ pull
           ▼                            ▼                ▼            ▼
┌──────────────────────────────────────────────────────────┐  ┌──────────────┐
│ [4] Oracle Cloud: VM.Standard.E5.Flex                    │  │ [6] Render   │
│     1 OCPU, 12 GB, Oracle Linux 10.2, IP 157.137.215.57  │  │ Web Service  │
│  ┌────────────────────────────────────────────────────┐  │  │ Free         │
│  │ Docker: contenedor taia_backend, puerto 8000       │  │  │ (respaldo)   │
│  │ Usuario | Academic | AI | Reminders                │  │  └──────┬───────┘
│  │ logs JSON a stdout, /health, /metrics              │  │         │
│  └────────────────────────────────────────────────────┘  │         │
│  ~/taia.env (escrito por cd.yml)                         │         │
└──────┬──────────────────┬──────────────────┬─────────────┘         │
       │ HTTPS            │ HTTPS            │ PostgreSQL            │ PostgreSQL
       ▼                  ▼                  ▼                       ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────────────┐
│ [7] Gemini   │   │ [8] Telegram │   │ [5] Supabase PostgreSQL              │
│ API (Google) │   │ Bot API      │   │ plan Free, región us-west-2          │
└──────────────┘   └──────────────┘   └──────────────────────────────────────┘

[1] Cliente (navegador, Swagger, futura app Flutter) ──HTTP :8000──► [4]
```

| # | Pieza | Dónde se ejecuta | Qué hace | Definida en |
|---|---|---|---|---|
| 1 | Cliente | Equipo del usuario (navegador o Swagger); la app Flutter es la arquitectura objetivo | Consume la API por HTTP | — |
| 2 | GitHub Actions | Runners `ubuntu-latest` de GitHub | CI: pruebas de contrato contra un PostgreSQL de servicio. CD: si el CI queda en verde sobre `main`, construye la imagen, la publica y la despliega por SSH | `.github/workflows/ci.yml`, `.github/workflows/cd.yml` |
| 3 | GitHub Container Registry | `ghcr.io/dei0811/taia_backend` | Guarda la imagen con dos etiquetas: los 12 primeros caracteres del SHA del commit y `latest` | `backend/Dockerfile` |
| 4 | API TAIA | Contenedor Docker en la VM `VM.Standard.E5.Flex` de OCI (1 OCPU, 12 GB, Oracle Linux 10.2) | Aplica las migraciones y sirve la API en el puerto 8000 | `backend/Dockerfile`, `terraform/` (la VM) |
| 5 | Base de datos | Supabase PostgreSQL, plan Free, región `us-west-2` | Persistencia de todos los módulos (RNF-06) | Migraciones en `backend/alembic/` |
| 6 | Respaldo en Render | Render Web Service Free | La misma imagen de GHCR (`latest` o una etiqueta fija) contra la misma base; no es el entorno principal | Panel de Render |
| 7 | Gemini API | Google | Proveedor LLM del módulo AI | `GEMINI_API_KEY`; aún no está configurada en el despliegue |
| 8 | Telegram Bot API | Telegram | Envío de notificaciones | `TAIA_TELEGRAM_BOT_TOKEN`; aún no está configurado en el despliegue |
| 9 | Terraform | Equipo del operador, con estado local | Describe la VM de OCI y la adopta mediante `import` | `terraform/` |

<<<<<<< HEAD
## 7.2. Flujo de despliegue
=======
El despliegue actual utiliza Docker Compose administrado por Dokploy. La API
publicada está disponible en el dominio sslip.io documentado arriba.

## 7.2. Corte vertical actualmente ejecutable

El despliegue remoto actual utiliza Docker Compose y Dokploy. La API publicada
está disponible en:

```text
http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io
```

El corte vertical actualmente ejecutable corresponde al **backend de TAIA ejecutado como una única aplicación FastAPI**. Puede ejecutarse localmente mediante Uvicorn y está desplegado para acceso remoto mediante Docker Compose y Dokploy.

Este corte integra los cuatro módulos actualmente implementados:

* **Usuario**
* **Academic**
* **AI**
* **Reminders**

La arquitectura mantiene un despliegue como **monolito modular**: los módulos se encuentran separados lógicamente dentro del código fuente, pero se ejecutan dentro del mismo proceso de aplicación.

### 7.2.1. Infraestructura de ejecución

El despliegue local actualmente utilizado puede representarse de la siguiente manera:
>>>>>>> migrate_to_dockploy

```text
push a main ─► CI (ci.yml) ─► verde ─► CD (cd.yml)
                                        ├─ build de backend/Dockerfile
                                        ├─ push a GHCR: <sha12> y latest
                                        ├─ SSH a la VM:
                                        │    escribe ~/taia.env desde los secretos
                                        │    docker pull, stop, rm, run
                                        └─ curl http://<VM>:8000/health, hasta 12 intentos
```

Un fallo en el CI impide el despliegue. Para volver a una versión anterior, se ejecuta el contenedor con una etiqueta anterior de GHCR, sin reconstruir la imagen.

## 7.3. Configuración y secretos

Las variables están declaradas en `.env.example`. En el despliegue, sus valores salen de los secretos de GitHub Actions y no del repositorio ni de la imagen.

| Variable | Obligatoria | Origen en el despliegue |
|---|---|---|
| `DATABASE_URL` | Sí; sin ella la API no arranca | Secreto de GitHub → `~/taia.env` |
| `TAIA_JWT_SECRET` | Sí; sin ella la API no arranca (RNF-02) | Secreto de GitHub → `~/taia.env` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | No | Sin configurar |
| `TAIA_TELEGRAM_BOT_TOKEN`, `TAIA_TELEGRAM_BOT_USERNAME` | No | Sin configurar |
| `GHCR_USERNAME`, `GHCR_PAT`, `OCI_HOST`, `OCI_USER`, `OCI_SSH_KEY` | Solo para `cd.yml` | Secretos de GitHub |

## 7.4. Observabilidad

- **Logs estructurados:** la API escribe una línea JSON por petición en stdout (`backend/app/shared/adapters/inbound/observability.py`), con los campos `timestamp`, `level`, `event`, `method`, `route`, `status`, `duration_ms` y `user_id`. Nunca incluye cuerpos ni tokens (RNF-05). Se consultan en la VM con `sudo docker logs taia_backend`.
- **Métrica:** `GET /metrics` devuelve `http_request_duration_p95_ms` por ruta, comparada con el objetivo de su escenario: `POST /ai/message` con **S3** (p95 ≤ 7 000 ms) y el resto con **RNF-08** (p95 < 500 ms). Se calcula sobre las últimas 1 000 peticiones por ruta y se reinicia con cada despliegue.

## 7.5. Entorno de desarrollo

En local, `run.bat` levanta la misma aplicación con Uvicorn contra un PostgreSQL local (`taia` y `taia_test`, igual que el servicio `postgres` del CI). El procedimiento está en el README.

## 7.6. Límites del despliegue actual

<<<<<<< HEAD
- La VM no es Always Free: cuesta 39,42 USD/mes (ADR-0003, arc42 §11).
- La API se expone por HTTP sin TLS, lo cual incumple RNF-04 hasta configurar un dominio y un proxy con HTTPS.
- Terraform describe la VM, pero no la VCN, la subred ni las reglas de seguridad, que siguen administradas desde la consola de OCI.
- Gemini y Telegram no están configurados en el despliegue; las funciones que no dependen de ellos funcionan (RNF-09).
- No hay un scheduler que dispare los recordatorios en su hora (S2).
=======
No existe actualmente un proceso independiente por módulo.

Esta decisión corresponde al estilo de **monolito modular** adoptado para el MVP.

### 7.2.3. Persistencia del corte actualmente ejecutable

El corte actual utiliza almacenamiento en memoria para permitir la ejecución local y las pruebas sin depender de una infraestructura de base de datos externa.

```text
FastAPI
   │
   ├── Usuario
   │      ├── InMemoryUserRepository
   │      └── InMemoryTelegramLinkRepository
   │
   ├── Academic
   │      └── InMemoryTaskRepository
   │
   ├── AI
   │      └── InMemoryConversationStore
   │
   └── Reminders
          └── InMemoryReminderRepository
```

Estas implementaciones son **volátiles**: los datos almacenados se pierden cuando se detiene o reinicia el proceso.

Por esta razón, este despliegue debe considerarse un **entorno de desarrollo y validación del corte vertical**, no todavía un despliegue productivo.

### 7.2.4. Dependencias externas

El backend contiene adaptadores preparados para comunicarse con servicios externos, pero estos no son necesarios para levantar y probar los recorridos internos principales.

| Dependencia          | Uso                         | Estado en el corte actual                                                          |
| -------------------- | --------------------------- | ---------------------------------------------------------------------------------- |
| **Gemini**           | Interpretación mediante LLM | Adaptador implementado; requiere configuración de credenciales para ejecución real |
| **Telegram Bot API** | Envío de notificaciones     | Adaptador implementado; requiere token del bot y vinculación de Telegram           |
| **PostgreSQL**       | Persistencia definitiva     | Previsto; no utilizado por el corte actual                                         |
| **Flutter**          | Cliente móvil               | Previsto; el backend puede probarse actualmente mediante Swagger/HTTP              |

La ausencia de Gemini o Telegram no impide iniciar el backend. Las funcionalidades que dependan directamente de estos servicios requieren su respectiva configuración.

### 7.2.5. Corte vertical funcional actualmente demostrable

El despliegue actual permite ejecutar y probar directamente mediante HTTP los siguientes recorridos:

```text
                         ┌──────────────┐
                         │   Usuario    │
                         │              │
                         │ registro     │
                         │ login        │
                         │ JWT          │
                         └──────┬───────┘
                                │
                         user_id autenticado
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
      ┌────────────┐     ┌────────────┐     ┌────────────┐
      │ Academic   │     │     AI     │     │ Reminders  │
      │            │     │            │     │            │
      │ tareas     │◄────│ gateway    │     │ reminders  │
      │            │     │            │────►│            │
      └─────┬──────┘     └────────────┘     └─────┬──────┘
            │                                     │
            ▼                                     ▼
     InMemoryTaskRepository             InMemoryReminderRepository
                                                   │
                                                   ▼
                                         Telegram Adapter*
```

`*` El envío efectivo hacia Telegram requiere la configuración del bot.

En consecuencia, el corte vertical actualmente ejecutable **ya no se limita al módulo Academic**. La infraestructura local permite levantar conjuntamente los cuatro módulos y probar sus interfaces HTTP y sus integraciones internas.

### 7.2.6. Integración interna entre módulos

La comunicación entre módulos ocurre dentro del mismo proceso y no mediante HTTP interno.

Las principales relaciones son:

```text
Usuario
   │
   └──► autenticación / user_id
          │
          ├────────► Academic
          │
          ├────────► AI
          │
          └────────► Reminders


AI
 │
 └──► AcademicGateway
          │
          └──► Academic


Reminders
 │
 └──► AcademicTaskLookup
          │
          └──► Academic
```

Este diseño evita introducir complejidad de red innecesaria dentro del monolito.

Los límites entre módulos se mantienen mediante **puertos, adaptadores y casos de uso**, mientras que el proceso de despliegue continúa siendo único.

### 7.2.7. Pruebas del despliegue actual

El corte vertical se valida mediante la suite automatizada del proyecto.

El estado actual registrado para esta versión es:

```text
74 passed
```

Las pruebas cubren los principales recorridos implementados de:

* autenticación;
* gestión académica;
* integración AI–Academic;
* gestión de recordatorios;
* aislamiento entre usuarios;
* notificaciones y adaptadores de Telegram.

La suite permite validar el comportamiento de los módulos sin requerir PostgreSQL, Gemini ni Telegram para los escenarios que no dependen directamente de estos servicios.

### 7.2.8. Límites del despliegue actual

El despliegue descrito no debe interpretarse como la arquitectura productiva definitiva.

Actualmente quedan fuera de este corte:

* persistencia permanente mediante PostgreSQL;
* despliegue distribuido o mediante contenedores;
* scheduler persistente para ejecutar automáticamente los recordatorios al llegar `scheduled_at`;
* aplicación Flutter integrada como cliente;
* configuración productiva de Gemini;
* configuración productiva del bot de Telegram;
* mecanismos de observabilidad y operación propios de producción.

La infraestructura actual tiene como objetivo **permitir la ejecución, integración y validación del MVP en un entorno local**, manteniendo la estructura modular necesaria para evolucionar posteriormente hacia una infraestructura productiva.

### 7.2.9. Evolución prevista del despliegue

La evolución prevista conserva los módulos dentro de un único backend inicialmente:

```text
                    Producción futura
                           │
                 ┌─────────▼─────────┐
                 │   TAIA Backend    │
                 │   FastAPI         │
                 │                   │
                 │ Usuario           │
                 │ Academic          │
                 │ AI                │
                 │ Reminders         │
                 └───────┬───────────┘
                         │
             ┌───────────┼──────────────┐
             │           │              │
             ▼           ▼              ▼
        PostgreSQL    Gemini       Telegram
```

La sustitución de los repositorios en memoria por PostgreSQL y la activación de los adaptadores externos permitirá evolucionar desde el corte local actual hacia un despliegue persistente.

No se contempla como objetivo inmediato separar los cuatro módulos en microservicios. La decisión actual mantiene un **monolito modular** para reducir la complejidad operacional durante el desarrollo del MVP.


## 7.3. Restricciones de despliegue

El despliegue debe respetar las siguientes restricciones:

* El backend debe poder ejecutarse con infraestructura gratuita durante el desarrollo académico.
* Las credenciales y secretos de servicios externos no deben almacenarse en el repositorio.
* La persistencia definitiva debe quedar aislada mediante `TaskRepository`, permitiendo reemplazar el repositorio en memoria por PostgreSQL.
* El proveedor de LLM debe permanecer aislado mediante un adaptador para facilitar su sustitución.
* La arquitectura debe considerar que una infraestructura gratuita puede suspender procesos por inactividad, especialmente para las funcionalidades de notificación programada.
* El backend debe ser el punto de control de acceso a los datos académicos; los servicios externos no acceden directamente a la base de datos.
>>>>>>> migrate_to_dockploy
