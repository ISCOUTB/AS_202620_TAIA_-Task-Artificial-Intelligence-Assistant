# 7. Vista de despliegue

TAIA se despliega como **un único contenedor** (monolito modular, [ADR-0001](../adr/0001-estilo-arquitectonico.md) y [ADR-0008](../adr/0008-mantener-monolito-sin-extraer-modulos.md)): el servicio `backend` de [`docker-compose.yml`](../../docker-compose.yml), administrado por Dokploy ([ADR-0010](../adr/0010-despliegue-con-dokploy-y-docker-compose.md)), contra una base Supabase PostgreSQL ([ADR-0004](../adr/0004-plataforma-base-de-datos.md)). El procedimiento de operación paso a paso está en la [guía de despliegue](../despliegue-dokploy.md); esta sección describe la estructura.

| | |
|---|---|
| URL pública | `https://taia-sistema.iscoutb.dev` |
| Health check | `GET https://taia-sistema.iscoutb.dev/health` → `200 {"status": "ok"}` |
| Métrica | `GET https://taia-sistema.iscoutb.dev/metrics` |
| Documentación interactiva | `https://taia-sistema.iscoutb.dev/docs` |
| Respaldo (alternativa del taller) | `https://taia-backend-latest.onrender.com`, con arranque en frío (53 s medidos el 2026-10-25) |

## 7.1. Infraestructura: una caja por pieza

```text
┌──────────────────────┐ git push ┌──────────────────────────────────────┐
│ Equipo de desarrollo │─────────►│ [2] GitHub Actions (ubuntu-latest)   │
└──────────────────────┘          │ ci.yml: pruebas, imagen, smoke test, │
                                  │         fronteras y Quality Gate     │
                                  │ cd.yml: POST al webhook de Dokploy   │
                                  └───────┬──────────────────────┬───────┘
                                          │ webhook (HTTPS)      │ consulta el gate
                                          ▼                      ▼
┌──────────────────────────────────────────────────────┐  ┌──────────────────┐
│ [3] Servidor con Dokploy                             │  │ [9] SonarCloud   │
│  Traefik: dominio y TLS ─► backend:8000              │  │ análisis automá- │
│  ┌────────────────────────────────────────────────┐  │  │ tico por commit  │
│  │ [4] Contenedor backend (Docker Compose)        │  │  └──────────────────┘
│  │ alembic upgrade head && uvicorn app.main:app   │  │
│  │ Usuario | Academic | AI | Reminders            │  │  ┌──────────────────┐
│  │ logs JSON a stdout, /health, /metrics          │  │  │ [6] Render       │
│  └────────────────────────────────────────────────┘  │  │ Web Service Free │
│  Environment de Dokploy ─► .env (env_file)           │  │ (respaldo)       │
└──────┬──────────────────┬──────────────────┬─────────┘  └────────┬─────────┘
       │ HTTPS            │ HTTPS            │ PostgreSQL          │ PostgreSQL
       ▼                  ▼                  ▼                     ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────────────┐
│ [7] Gemini   │   │ [8] Telegram │   │ [5] Supabase PostgreSQL              │
│ API (Google) │   │ Bot API      │   │ plan Free, región us-west-2, pooler  │
└──────────────┘   └──────────────┘   └──────────────────────────────────────┘

[1] Cliente (navegador, Swagger, futura app Flutter) ──HTTPS──► [3] Traefik ──► [4]
```

| # | Pieza | Dónde se ejecuta | Qué hace | Definida en |
|---|---|---|---|---|
| 1 | Cliente | Equipo del usuario (navegador o Swagger); la app Flutter es la arquitectura objetivo | Consume la API por HTTPS | — |
| 2 | GitHub Actions | Runners `ubuntu-latest` de GitHub | CI: pruebas contra un PostgreSQL 17 de servicio, construcción y arranque de la imagen, fronteras, cliente OpenAPI y Quality Gate. CD: si el CI de un push a `main` queda en verde y su SHA sigue siendo el último, llama al webhook de Dokploy | [`ci.yml`](../../.github/workflows/ci.yml), [`cd.yml`](../../.github/workflows/cd.yml) |
| 3 | Servidor con Dokploy | Servidor administrado por el equipo | Clona `main`, construye la imagen, guarda las variables en Environment, publica el dominio con TLS mediante Traefik y muestra despliegues y logs | Configuración del servicio en Dokploy ([guía](../despliegue-dokploy.md)) |
| 4 | API TAIA | Contenedor `backend` de Docker Compose, puerto interno 8000 sin publicar en el host, `restart: unless-stopped` | Aplica las migraciones al arrancar y sirve la API; health check de Compose cada 30 s sobre `/health` | [`docker-compose.yml`](../../docker-compose.yml), [`backend/Dockerfile`](../../backend/Dockerfile) |
| 5 | Base de datos | Supabase PostgreSQL, plan Free, región `us-west-2` | Persistencia de los cuatro módulos en una base y un esquema compartidos (RNF-06, [ADR-0009](../adr/0009-base-compartida-con-referencias-logicas-entre-modulos.md)) | Migraciones en `backend/alembic/` |
| 6 | Respaldo en Render | Render Web Service Free | Alternativa del taller ([ADR-0003](../adr/0003-plataforma-despliegue-api.md)); responde, pero no es el entorno principal ni lo actualiza el CD | Panel de Render |
| 7 | Gemini API | Google | Proveedor LLM del módulo AI | `GEMINI_API_KEY` en Environment |
| 8 | Telegram Bot API | Telegram | Envío de notificaciones con `sendMessage`; recepción de updates del bot en `POST /telegram/webhook`, que por ahora solo confirma la vinculación | `TAIA_TELEGRAM_BOT_TOKEN` y `TAIA_WEBHOOK_SECRET` en Environment (opcionales), [`telegram_bot_client.py`](../../backend/app/modules/reminders/adapters/outbound/telegram_bot_client.py), [`telegram_webhook.py`](../../backend/app/modules/usuario/adapters/inbound/telegram_webhook.py) |
| 9 | SonarCloud | Organización `isco-utb`, proyecto público | Análisis estático automático de cada commit; el job `quality-gate` del CI falla si el gate no está en `OK` | [`.sonarcloud.properties`](../../.sonarcloud.properties) |

No hay broker de mensajes ni caché: las integraciones son HTTP síncronas ([ADR-0002](../adr/0002-estrategia-integracion-api-sincrona.md)) y las lecturas van directo a PostgreSQL ([arc42 §8.11](08-conceptos-transversales.md#811-caché)).

## 7.2. Flujo de despliegue

```text
push a main ─► CI (ci.yml)
                 ├─ build de backend/Dockerfile (sin publicar)
                 ├─ pytest contra postgres:17
                 ├─ smoke test: la imagen migra una base vacía y responde
                 ├─ fronteras, dependencias y cliente OpenAPI sincronizado
                 └─ quality-gate: espera el análisis de SonarCloud del mismo SHA
               verde ─► CD (cd.yml)
                 ├─ ¿el SHA probado sigue siendo el último de main? si no, termina
                 └─ POST a DOKPLOY_WEBHOOK_URL
                      ─► Dokploy: git clone main, docker compose build/up
                      ─► alembic upgrade head && uvicorn
                      ─► health check de Compose sobre /health
```

Un fallo en el CI o en el Quality Gate impide el despliegue. Un CD verde indica que Dokploy **aceptó la solicitud**, no que el despliegue terminó: el resultado se comprueba en *Deployments* de Dokploy, sus logs y `/health`. El webhook no transmite el SHA, así que Dokploy construye la cabeza de `main` en el momento del clone.

Para volver a una versión anterior se revierte el cambio en Git y se deja que pase por CI y CD. Antes debe comprobarse que el código revertido es compatible con las migraciones ya aplicadas: revertir código no revierte el esquema.

## 7.3. Configuración y secretos

Las variables están declaradas en [`.env.example`](../../.env.example). En el despliegue, sus valores viven en **Environment** de Dokploy, que las escribe en un `.env` junto a `docker-compose.yml`; Compose las carga con `env_file`. No están en el repositorio, ni en la imagen, ni pasan por GitHub Actions.

| Variable | Obligatoria | Dónde vive |
|---|---|---|
| `DATABASE_URL` | Sí; Compose no arranca sin ella | Environment de Dokploy |
| `TAIA_JWT_SECRET` | Sí; Compose no arranca sin ella (RNF-02) | Environment de Dokploy |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | La clave sí: `app/main.py` compone el adaptador al importar | Environment de Dokploy |
| `TAIA_TELEGRAM_BOT_TOKEN`, `TAIA_TELEGRAM_BOT_USERNAME` | No; sin ellas el bot no responde y el resto funciona (RNF-09) | Environment de Dokploy |
| `DOKPLOY_WEBHOOK_URL` | Solo para `cd.yml` | Secreto de GitHub Actions |

## 7.4. Observabilidad

- **Logs estructurados:** la API escribe una línea JSON por petición en stdout ([`observability.py`](../../backend/app/shared/adapters/inbound/observability.py)), con los campos `timestamp`, `level`, `event`, `method`, `route`, `status`, `duration_ms` y `user_id`. Nunca incluye cuerpos ni tokens (RNF-05). Se consultan en la pestaña *Logs* del servicio en Dokploy.
- **Métrica:** `GET /metrics` devuelve `http_request_duration_p95_ms` por ruta, comparada con el objetivo de su escenario: `POST /ai/message` con **S3** (p95 ≤ 7 000 ms) y el resto con **RNF-08** (p95 < 500 ms). Se calcula en memoria sobre las últimas 1 000 peticiones por ruta y se reinicia con cada despliegue.
- **Salud:** el health check de Compose consulta `/health` cada 30 s (60 s de gracia al arrancar, 3 reintentos); Dokploy muestra el estado *healthy* del contenedor.

## 7.5. Entorno de desarrollo

En local, `run.bat` levanta la misma aplicación con Uvicorn contra un PostgreSQL local (`taia` y `taia_test`, igual que el servicio `postgres` del CI). También se puede levantar la imagen con Docker Compose, un `.env` en la raíz y un `docker-compose.local.yml` personal (no versionado) que publique el puerto, como indica la [guía de despliegue](../despliegue-dokploy.md#ejecutar-con-compose-localmente). El procedimiento está en el [README](../../README.md).

## 7.6. Límites del despliegue actual

- **Un solo contenedor:** un fallo del proceso afecta a los cuatro módulos a la vez, y no se escalan por separado ([ADR-0008](../adr/0008-mantener-monolito-sin-extraer-modulos.md)).
- **CD sin confirmación:** el workflow no espera a que Dokploy termine ni comprueba la revisión desplegada (ver §7.2).
- **Supabase Free:** pausa el proyecto tras una semana sin actividad y la API falla hasta reactivarlo ([arc42 §11](11-riesgos-y-deudas-tecnicas.md)).
- **Métrica volátil:** `/metrics` se pierde en cada reinicio; no hay un sistema de métricas persistente ni alertas.
- **Sin scheduler:** no hay un proceso que dispare los recordatorios en su hora (S2, `RF-NOT-02`); el envío ocurre con `POST /reminders/{id}/notify`.
- **Costo del servidor:** usar Dokploy no fija el costo del servidor que lo aloja; la facturación real debe verificarse ([costo_mensual.md](../costo_mensual.md), [ADR-0010](../adr/0010-despliegue-con-dokploy-y-docker-compose.md)).
