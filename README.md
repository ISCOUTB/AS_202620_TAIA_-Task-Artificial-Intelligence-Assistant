# TAIA - Task Artificial Intelligence Assistant

Sistema de gestión académica para estudiantes universitarios, apoyado por inteligencia artificial y comunicación mediante lenguaje natural.

## Sistema desplegado

| | |
|---|---|
| API | http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io |
| Health check | http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io/health → `200 {"status": "ok"}` |
| Métrica de latencia | http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io/metrics |
| Documentación interactiva | http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io/docs |
| Respaldo en Render (alternativa del taller) | https://taia-backend-latest.onrender.com/health |

La API corre en una VM de Oracle Cloud con Docker y usa Supabase PostgreSQL. Cada push a `main` que pasa el CI se despliega automáticamente. El detalle está en [arc42 §7](docs/arc42/07-vista-de-despliegue.md).

Comprobación desde cualquier red:

```bash
curl -sS -o /dev/null -w 'http=%{http_code} tiempo=%{time_total}s\n' http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io/health
```

## Integrantes

- Valeria Berrio Payares
- Deiner Gonzalez Paredes
- Luis Mendoza Angulo
- Mark Pastrana Koreia

## Descripción

El Asistente Académico Inteligente busca facilitar la organización de la vida académica de los estudiantes universitarios mediante una interfaz móvil y un bot de Telegram.

El estudiante podrá registrar información académica utilizando mensajes en lenguaje natural. Por ejemplo:

> "Tengo que entregar el proyecto de programación el próximo lunes."

El sistema utilizará Gemini para interpretar el mensaje, identificar la intención y transformar la información en datos estructurados. Posteriormente, el backend validará la información y la almacenará en PostgreSQL.

La información registrada podrá ser consultada y gestionada desde la aplicación desarrollada en Flutter.

## Funcionalidades del MVP

- Gestión de materias.
- Registro de tareas.
- Registro de exámenes.
- Calendario académico.
- Recordatorios.
- Dashboard académico.
- Captura de información mediante Telegram.
- Interpretación de lenguaje natural mediante Gemini.

## Tecnologías

- **Flutter:** aplicación móvil.
- **FastAPI:** backend y API del sistema.
- **PostgreSQL:** almacenamiento de información académica (Supabase en el despliegue).
- **Gemini:** interpretación de lenguaje natural y asistencia conversacional.
- **Telegram Bot API:** canal de captura rápida de información.
- **Docker, GitHub Actions, GHCR, Oracle Cloud y Terraform:** despliegue.

## Estado actual

El backend es un **monolito modular con organización hexagonal selectiva** con los módulos **Usuario, Academic, Reminders y AI**, persistido en PostgreSQL con migraciones de Alembic.

| Integración | Estado |
|---|---|
| PostgreSQL | Integrada. Supabase en el despliegue y PostgreSQL local en desarrollo y CI. |
| Telegram | Vinculación de cuenta y envío de notificaciones implementados; en el despliegue falta configurar `TAIA_TELEGRAM_BOT_TOKEN`. |
| Gemini | Puerto y adaptador implementados; en el despliegue falta configurar `GEMINI_API_KEY`. |
| Flutter | Arquitectura objetivo; no forma parte del backend entregado. |

El estado por requerimiento está en `docs/requerimientos.md`. Las rutas de la API están en `/docs` y en el contrato `docs/api/openapi.json`.

## Arquitectura

Los módulos están en `backend/app/modules/`:

- `usuario`: identidad, JWT y vinculación con Telegram.
- `academic`: materias, períodos, horarios y tareas.
- `reminders`: recordatorios y notificaciones.
- `ai`: conversaciones y abstracción del proveedor LLM.

Cada módulo separa `domain`, `application` (puertos y casos de uso) y `adapters`. Decisiones:

- [ADR-0001 — Estilo arquitectónico](docs/adr/0001-estilo-arquitectonico.md)
- [ADR-0002 — Integración HTTP síncrona con OpenAPI](docs/adr/0002-estrategia-integracion-api-sincrona.md)
- [ADR-0003 — Plataforma de despliegue de la API](docs/adr/0003-plataforma-despliegue-api.md)
- [ADR-0004 — Plataforma de la base de datos](docs/adr/0004-plataforma-base-de-datos.md)
- [ADR-0005 — Normalización de la confirmación escrita en español](docs/adr/0005-normalizacion-confirmacion-espanol.md)

## Documentación

- [Despliegue con Docker Compose y Dokploy](docs/despliegue-dokploy.md):
  configuración del servicio, variables, dominio HTTPS y CD mediante la API de Dokploy.
- [Infraestructura con Terraform en OCI](terraform/README.md): configuración local,
  opcional para administrar el servidor existente; independiente de Dokploy.

La documentación del proyecto se encuentra en la carpeta docs/.

- docs/ficha_problema.md — descripción del problema y propuesta de solución.
- docs/aspectos.md — aspectos arquitectónicos y trazabilidad.
- docs/ia.md — registro del uso de inteligencia artificial.
- docs/arc42/ — documentación de arquitectura mediante arc42.
- docs/c4/ — diagramas de arquitectura C4.
- docs/calidad/ — atributos y escenarios de calidad.
- docs/adr/ — decisiones arquitectónicas.

La API desplegada está disponible en:

- API: http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io
- Documentación interactiva: http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io/docs
- Health check: http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io/health

## Requisitos

### Docker Compose / Dokploy

El despliegue actual de la API está publicado en
`http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io`.

El archivo `docker-compose.yml` construye `backend/Dockerfile`. Configurar
`DATABASE_URL` (PostgreSQL) y `TAIA_JWT_SECRET` siguiendo `.env.example`.
Para Dokploy, seleccionar `./docker-compose.yml` y configurar el dominio del
servicio `backend` en el puerto interno `8000`.

Para ejecutar localmente, copiar `.env.example` a `.env`, completar los valores y usar:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build -d
```

La API estará en `http://127.0.0.1:8000/docs`. PostgreSQL se configura por separado.
Consultar la [guía de despliegue](docs/despliegue-dokploy.md) para redes, secrets y CI/CD.

### Ejecución directa con Python

Para ejecutar el proyecto se requiere:

Python 3.14 o compatible.
Las dependencias especificadas en backend/requirements.txt.

### Instalar las dependencias:

pip install -r backend/requirements.txt

### Ejecución

El proyecto cuenta con un backend ejecutable del monolito modular.

Desde la raíz del repositorio, en Windows:

```bat
.\run.bat
```

`run.bat` no fija ninguna credencial. Lee la configuración de `backend/.env`, comprueba que exista y que `GEMINI_API_KEY` tenga valor, aplica las migraciones y levanta Uvicorn en http://127.0.0.1:8000. Las variables y su significado están en [`.env.example`](.env.example), que sí se versiona porque no contiene secretos.

La plantilla se copia una vez:

```bat
copy .env.example backend\.env
```

Si el arranque se rechaza con `GEMINI_API_KEY vacío`, la clave se obtiene en https://aistudio.google.com/apikey. Es obligatoria: la composición del adaptador de Gemini ocurre en `app/main.py`, así que sin ella el proceso no arranca en lugar de servir un servicio inservible.

## Pruebas

```bash
python -m pytest
```

Las pruebas de integración con PostgreSQL se omiten si no está `TEST_DATABASE_URL`:

```bash
TEST_DATABASE_URL=postgresql+psycopg://usuario@localhost:5432/taia_test python -m pytest
```

`TEST_DATABASE_URL` debe apuntar a una base distinta de la de desarrollo: `backend/tests/conftest.py` ejecuta `alembic downgrade base` y `TRUNCATE` al iniciar la sesión.

Contrato de la API (lo mismo que ejecuta el CI):

```bash
python -m pytest backend/tests/test_api_contract.py -q
python tools/generate_api_client.py
git diff --exit-code -- backend/generated/taia_api_client.py
```

## Despliegue

El entorno se recrea con estos pasos. Los valores reales de las variables nunca se guardan en el repositorio.

### 1. Base de datos

1. Crear un proyecto en Supabase (plan Free) y copiar la cadena de conexión del *pooler* (Project Settings > Database).
2. Esa cadena es el valor de `DATABASE_URL`. Las tablas las crea la API al arrancar con `alembic upgrade head`.

### 2. VM en Oracle Cloud

1. Crear una instancia de cómputo en OCI con Oracle Linux, abrir el puerto 8000 en la lista de seguridad de la subred y en el firewall del sistema, y configurar el acceso por SSH con una clave.
2. Instalar Docker en la VM (paquetes de Oracle Linux) y habilitarlo con `sudo systemctl enable --now docker`.
3. Adoptar la instancia en Terraform siguiendo [terraform/README.md](terraform/README.md): completar `terraform.tfvars` con los datos de la instancia, `terraform init`, `terraform import` y un `terraform plan` sin cambios.

### 3. Secretos de GitHub Actions

En *Settings > Secrets and variables > Actions* del repositorio:

| Secreto | Valor |
|---|---|
| `DATABASE_URL` | Cadena de conexión de Supabase |
| `TAIA_JWT_SECRET` | Valor aleatorio largo: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `GHCR_USERNAME`, `GHCR_PAT` | Usuario y token con `write:packages` para publicar en GHCR |
| `OCI_HOST`, `OCI_USER`, `OCI_SSH_KEY` | IP pública de la VM, usuario (`opc`) y clave privada SSH |

### 4. Desplegar

Hacer push a `main`. El workflow [CI](.github/workflows/ci.yml) ejecuta las pruebas y, si queda en verde, [CD](.github/workflows/cd.yml) hace lo siguiente:

1. Construye `backend/Dockerfile` y publica `ghcr.io/dei0811/taia_backend:<sha12>` y `:latest`.
2. Por SSH, escribe `~/taia.env` en la VM con los secretos y reemplaza el contenedor `taia_backend` (puerto 8000, `--restart unless-stopped`).
3. Comprueba `GET /health` desde fuera de la VM, con hasta 12 intentos.

### 5. Volver a una versión anterior

En la VM, ejecutar el contenedor con una etiqueta anterior de GHCR:

```bash
sudo docker stop taia_backend && sudo docker rm taia_backend
sudo docker run -d --name taia_backend --env-file ~/taia.env -p 8000:8000 \
  --restart unless-stopped ghcr.io/dei0811/taia_backend:<sha12-anterior>
```

## Observabilidad

- **Logs estructurados:** una línea JSON por petición en stdout, con `timestamp`, `level`, `event`, `method`, `route`, `status`, `duration_ms` y `user_id`. Nunca incluye cuerpos ni tokens (RNF-05). En la VM se consultan con `sudo docker logs taia_backend --tail 20`. Ejemplo:

  ```json
  {"timestamp": "2026-09-27T22:31:11.820-05:00", "level": "INFO", "logger": "taia", "event": "http_request", "method": "GET", "route": "/health", "status": 200, "duration_ms": 3.0, "user_id": null}
  ```

- **Métrica:** `GET /metrics` devuelve `http_request_duration_p95_ms` por ruta, comparada con el objetivo de su escenario de calidad: `POST /ai/message` con **S3** (p95 ≤ 7 s) y el resto con **RNF-08** (p95 < 500 ms). Se calcula sobre las últimas 1 000 peticiones por ruta desde el último despliegue.

## Costo

El despliegue cuesta **39,42 USD/mes**, todo por la VM `VM.Standard.E5.Flex`, que no es Always Free. Supabase, GHCR y GitHub Actions quedan en 0 USD con el volumen supuesto. El volumen, el costo por pieza y el punto de ruptura de cada capa gratuita están en [docs/costo_mensual.md](docs/costo_mensual.md).

## Documentación

- `docs/requerimientos.md`: requerimientos (fuente de verdad).
- `docs/diccionario_datos.md`: datos y restricciones.
- `docs/arc42/`: arquitectura (arc42).
- `docs/adr/`: decisiones arquitectónicas.
- `docs/c4/`: diagramas C4.
- `docs/calidad/`: atributos y escenarios de calidad.
- `docs/costo_mensual.md`: estimación de costo.
- `docs/api/openapi.json`: contrato de la API.
- `terraform/README.md`: infraestructura en OCI.
- `docs/ia.md`: registro del uso de inteligencia artificial..
