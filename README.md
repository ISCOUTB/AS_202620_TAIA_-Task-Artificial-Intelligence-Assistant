# TAIA - Task Artificial Intelligence Assistant

Asistente académico para estudiantes universitarios: organiza asignaturas, horario, tareas y exámenes, avisa con recordatorios y entiende mensajes en lenguaje natural desde la aplicación móvil o desde Telegram.

## Sistema desplegado

| | |
|---|---|
| API | https://taia-sistema.iscoutb.dev |
| Health check | https://taia-sistema.iscoutb.dev/health → `200 {"status": "ok"}` |
| Métrica de latencia | https://taia-sistema.iscoutb.dev/metrics |
| Documentación interactiva | https://taia-sistema.iscoutb.dev/docs |
| CI y CD (GitHub Actions) | https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions |
| Análisis estático y Quality Gate (SonarCloud, público) | https://sonarcloud.io/project/overview?id=ISCOUTB_AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant |

La API corre en Dokploy con Docker Compose y usa Supabase PostgreSQL. Cada push a `main` ejecuta el CI; si queda en verde, el CD le pide a Dokploy que despliegue.

Comprobación desde cualquier red:

```bash
curl -sS -o /dev/null -w 'http=%{http_code} tiempo=%{time_total}s\n' https://taia-sistema.iscoutb.dev/health
```

## Integrantes

- Valeria Berrio Payares
- Deiner Gonzalez Paredes
- Luis Mendoza Angulo
- Mark Pastrana Koreia

## Descripción

El estudiante registra su vida académica con formularios en la aplicación o con mensajes en lenguaje natural, por ejemplo:

> "Tengo que entregar el proyecto de programación el próximo lunes."

El agente interpreta el mensaje con un modelo de lenguaje (Groq como proveedor principal y Gemini como respaldo), propone la acción y solo la guarda cuando el estudiante responde "sí". El modelo nunca escribe en la base de datos: el backend valida los datos y los guarda en PostgreSQL. Si ningún proveedor responde, TAIA avisa y no hace nada.

## Funcionalidades

- **Cuenta:** registro con autorización de datos, inicio de sesión, recuperación de contraseña por correo, configuración y desactivación de la cuenta.
- **Configuración inicial:** período académico, asignaturas y horario de clases, en pasos.
- **Asignaturas y horario:** asignaturas con alias para el chat; una clase se registra de una vez en varios días, cada uno con su hora.
- **Actividades:** tareas y exámenes con prioridad calculada por la fecha límite y estado vencido.
- **Recordatorios y notificaciones:** recordatorios por defecto o personalizados, notificaciones push con Firebase y bandeja de notificaciones.
- **Agenda:** vistas de día, semana y mes con clases, sesiones de estudio y actividades.
- **Plan de estudio:** plan de 7 días a partir del horario, las actividades pendientes y un formulario de preferencias.
- **Perfil:** estadísticas de rendimiento.
- **Agente conversacional:** crear, consultar, editar y completar actividades, resúmenes, horario y ayuda sobre la aplicación, desde la app y desde Telegram.
- **Tutorial:** recorrido de la aplicación la primera vez, que se puede repetir.

El estado de cada requerimiento está en [`docs/requerimientos.md`](docs/requerimientos.md).

## Tecnologías

- **Flutter:** aplicación móvil (`frontend/`).
- **FastAPI, Pydantic, SQLAlchemy y Alembic:** backend (`backend/`).
- **PostgreSQL:** Supabase en el despliegue, PostgreSQL local en desarrollo y CI.
- **Groq y Gemini:** interpretación de lenguaje natural, ayuda y plan de estudio.
- **Telegram Bot API:** canal conversacional.
- **Firebase Cloud Messaging:** notificaciones push.
- **Resend:** correo de recuperación de contraseña.
- **Docker Compose, Dokploy, GitHub Actions y SonarCloud:** integración y despliegue continuos.

## Arquitectura

El backend es un **monolito modular con organización hexagonal selectiva**. Los módulos están en `backend/app/modules/`:

- `usuario`: identidad, sesión con JWT, perfil, dispositivos para push, recuperación de contraseña y vinculación con Telegram.
- `academic`: asignaturas, período, horario, actividades, calendario, estadísticas y plan de estudio.
- `reminders`: recordatorios, envío periódico de notificaciones push y bandeja.
- `ai`: agente conversacional, contrato con el modelo de lenguaje y respaldo entre proveedores (`FallbackLLM`).

Cada módulo separa `domain`, `application` (puertos y casos de uso) y `adapters`. Los módulos solo se comunican por los puertos de entrada del módulo dueño, y cada tabla tiene un único módulo que la escribe.

La documentación de arquitectura está en [`docs/arc42/`](docs/arc42/) y los diagramas C4 en [`docs/c4/`](docs/c4/).

### Decisiones arquitectónicas

- [ADR-0001: Monolito modular con organización hexagonal selectiva](docs/adr/0001-estilo-arquitectonico.md)
- [ADR-0002: Integración HTTP síncrona con contrato OpenAPI](docs/adr/0002-estrategia-integracion-api-sincrona.md)
- [ADR-0003: Despliegue en una VM de OCI con Docker](docs/adr/0003-plataforma-despliegue-api.md) (reemplazado por ADR-0010)
- [ADR-0004: Base de datos en Supabase PostgreSQL](docs/adr/0004-plataforma-base-de-datos.md)
- [ADR-0005: Normalización de la confirmación escrita en español](docs/adr/0005-normalizacion-confirmacion-espanol.md)
- [ADR-0006: Fronteras y evaluación verificable](docs/adr/0006-fronteras-y-evaluacion-verificable.md)
- [ADR-0007: Comportamiento ante fallo del proveedor LLM](docs/adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md) (punto 4 reemplazado por ADR-0011)
- [ADR-0008: Mantener el monolito sin extraer módulos](docs/adr/0008-mantener-monolito-sin-extraer-modulos.md)
- [ADR-0009: Base compartida con referencias lógicas entre módulos](docs/adr/0009-base-compartida-con-referencias-logicas-entre-modulos.md)
- [ADR-0010: Despliegue con Dokploy y Docker Compose](docs/adr/0010-despliegue-con-dokploy-y-docker-compose.md)
- [ADR-0011: Groq como proveedor LLM de respaldo](docs/adr/0011-usar-groq-como-proveedor-llm-de-respaldo.md) (orden reemplazado por ADR-0013)
- [ADR-0012: Recordatorios con un proceso periódico dentro de la API](docs/adr/0012-enviar-recordatorios-con-un-proceso-dentro-de-la-api.md)
- [ADR-0013: Groq como proveedor principal y Gemini como respaldo](docs/adr/0013-usar-groq-como-proveedor-llm-principal.md)

## Ejecución local

### Backend

Requisitos: Python 3.12 (la versión de la imagen Docker y del CI) y PostgreSQL.

```bash
pip install -r backend/requirements.txt
```

En Windows, desde la raíz del repositorio:

```bat
copy .env.example backend\.env
.\run.bat
```

`run.bat` no fija ninguna credencial. Lee la configuración de `backend/.env`, comprueba que exista y que `GEMINI_API_KEY` tenga valor, aplica las migraciones y levanta Uvicorn en http://127.0.0.1:8000. Las variables y su significado están en [`.env.example`](.env.example).

La API exige `DATABASE_URL`, `TAIA_JWT_SECRET` y `GEMINI_API_KEY`, y no arranca sin ellas. La clave de Gemini se obtiene en https://aistudio.google.com/apikey. Las demás variables son opcionales:

| Variables | Sin ellas |
|---|---|
| `GROQ_API_KEY_1`, `GROQ_API_KEY_2`, `GROQ_MODEL` | Solo se usa Gemini. |
| `TAIA_TELEGRAM_BOT_TOKEN`, `TAIA_TELEGRAM_BOT_USERNAME`, `TAIA_WEBHOOK_SECRET` | No hay canal de Telegram. |
| `RESEND_API`, `RESEND_FROM` | La recuperación de contraseña responde `503`. |
| `FIREBASE_CREDENTIALS_JSON` | No hay notificaciones push; quedan en la bandeja. |

Con Docker Compose: copiar `.env.example` a `.env`, crear el `docker-compose.local.yml` personal que publica el puerto (su contenido está en la [guía de despliegue](docs/despliegue-dokploy.md#ejecutar-con-compose-localmente)) y ejecutar:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build -d
```

### Aplicación móvil

Requisitos: Flutter con Dart 3.13 o superior.

```bash
cd frontend
flutter pub get
flutter run
```

Por defecto la aplicación usa la API desplegada. Para usar la API local desde el emulador de Android:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

APK de release para Android, con las arquitecturas arm64-v8a, armeabi-v7a y x86_64:

```bash
flutter build apk --release
```

## Pruebas

Backend, desde la raíz (requiere una base de pruebas distinta de la de desarrollo, porque se vacía en cada prueba):

```bash
TEST_DATABASE_URL=postgresql+psycopg://taia:taia@localhost:5432/taia_test GEMINI_API_KEY=test python -m pytest
```

Ninguna prueba llama a un modelo de lenguaje real: Gemini y Groq se prueban con respuestas simuladas.

Contrato de la API (lo mismo que ejecuta el CI):

```bash
python -m pytest backend/tests/test_api_contract.py -q
python tools/generate_api_client.py
git diff --exit-code -- backend/generated/taia_api_client.py
```

Aplicación móvil:

```bash
cd frontend
flutter analyze
flutter test
```

Evaluación del modelo de lenguaje contra el dataset de [`docs/evaluacion_ia/`](docs/evaluacion_ia/) (usa las claves reales y consume cuota):

```bash
python tools/eval_llm.py --dry-run          # valida el dataset sin llamar al modelo
python tools/eval_llm.py                    # Gemini
python tools/eval_llm.py --proveedor groq   # Groq
```

## Despliegue

Los valores reales de las variables nunca se guardan en el repositorio. El procedimiento completo está en la [guía de despliegue](docs/despliegue-dokploy.md).

1. **Base de datos:** crear un proyecto en Supabase y copiar la cadena de conexión del *pooler* como `DATABASE_URL`. Las tablas las crea la API al arrancar con `alembic upgrade head`.
2. **Dokploy:** crear un servicio Docker Compose con `./docker-compose.yml`, publicar el dominio del servicio `backend` en el puerto interno `8000` con HTTPS y configurar las variables de la aplicación en **Environment**.
3. **GitHub Actions:** guardar en *Settings > Secrets and variables > Actions* el secreto `DOKPLOY_WEBHOOK_URL`, el webhook del servicio en Dokploy. Las variables de la aplicación no van en GitHub.
4. **Desplegar:** hacer push a `main`.
   - El [CI](.github/workflows/ci.yml) ejecuta las pruebas contra un PostgreSQL efímero, construye y arranca la imagen, compara el contrato de la API, audita las dependencias y espera el Quality Gate de SonarCloud.
   - Si el CI queda en verde y su commit sigue siendo el último de `main`, el [CD](.github/workflows/cd.yml) llama al webhook y Dokploy clona `main`, construye y despliega.
   - Un CD en verde solo significa que Dokploy recibió el aviso. El despliegue se confirma en Dokploy y en `/health`.

## Observabilidad

- **Logs estructurados:** una línea JSON por petición en la salida estándar, con `timestamp`, `level`, `event`, `method`, `route`, `status`, `duration_ms` y `user_id`. Nunca incluye cuerpos ni tokens (RNF-05). Se consultan en los logs del servicio en Dokploy. Ejemplo:

  ```json
  {"timestamp": "2026-09-27T22:31:11.820-05:00", "level": "INFO", "logger": "taia", "event": "http_request", "method": "GET", "route": "/health", "status": 200, "duration_ms": 3.0, "user_id": null}
  ```

- **Métrica:** `GET /metrics` devuelve `http_request_duration_p95_ms` por ruta, comparada con el objetivo de su escenario de calidad: `POST /ai/message` con **S3** (p95 ≤ 7 s) y el resto con **RNF-08** (p95 < 500 ms). Se calcula sobre las últimas 1000 peticiones por ruta desde el último despliegue.

## Costo

Ver la estimación en [`docs/costo_mensual.md`](docs/costo_mensual.md).

## Documentación

- [`docs/requerimientos.md`](docs/requerimientos.md): requerimientos, la fuente de verdad del sistema.
- [`docs/diccionario_datos.md`](docs/diccionario_datos.md): datos y restricciones.
- [`docs/ficha_problema.md`](docs/ficha_problema.md): problema y propuesta de solución.
- [`docs/aspectos.md`](docs/aspectos.md): aspectos arquitectónicos y trazabilidad.
- [`docs/arc42/`](docs/arc42/): arquitectura.
- [`docs/adr/`](docs/adr/): decisiones arquitectónicas.
- [`docs/c4/`](docs/c4/): diagramas C4.
- [`docs/modelo_amenazas.md`](docs/modelo_amenazas.md): amenazas y mitigaciones.
- [`docs/calidad/`](docs/calidad/): atributos y escenarios de calidad.
- [`docs/evaluacion_ia/`](docs/evaluacion_ia/): dataset y resultados de la evaluación del modelo de lenguaje.
- [`docs/politica_privacidad.md`](docs/politica_privacidad.md): política de tratamiento de datos que se acepta al registrarse.
- [`docs/despliegue-dokploy.md`](docs/despliegue-dokploy.md): despliegue con Docker Compose y Dokploy.
- [`docs/costo_mensual.md`](docs/costo_mensual.md): estimación de costo.
- [`docs/api/openapi.json`](docs/api/openapi.json): contrato de la API.
- [`docs/ia.md`](docs/ia.md): registro del uso de inteligencia artificial.
