# 7. Vista de despliegue

TAIA se despliega como un **único contenedor** (monolito modular, ADR-0001) en una VM de Oracle Cloud, con la base de datos en Supabase. El despliegue es automático desde `main`. Las decisiones de plataforma están en [ADR-0003](../adr/0003-plataforma-despliegue-api.md) (API) y [ADR-0004](../adr/0004-plataforma-base-de-datos.md) (base de datos), y el costo en [costo_mensual.md](../costo_mensual.md).

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

## 7.2. Flujo de despliegue

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

- La VM no es Always Free: cuesta 39,42 USD/mes (ADR-0003, arc42 §11).
- La API se expone por HTTP sin TLS, lo cual incumple RNF-04 hasta configurar un dominio y un proxy con HTTPS.
- Terraform describe la VM, pero no la VCN, la subred ni las reglas de seguridad, que siguen administradas desde la consola de OCI.
- Gemini y Telegram no están configurados en el despliegue; las funciones que no dependen de ellos funcionan (RNF-09).
- No hay un scheduler que dispare los recordatorios en su hora (S2).
