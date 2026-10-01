# Despliegue de TAIA con Dokploy

`docker-compose.yml` construye `backend/Dockerfile` desde la raíz del repositorio.
Ejecuta un servicio `backend` en el puerto interno **8000**, con reinicio automático
y health check en `/health`. El arranque aplica `alembic upgrade head` antes de
iniciar Uvicorn. PostgreSQL debe estar disponible y la base de datos debe existir.

## Configurar Dokploy

1. Crear un servicio **Docker Compose** en el proyecto de Dokploy. Seleccionar
   el repositorio Git y la rama `main`, con Compose Path `./docker-compose.yml`.
   Usar modo Compose: el modo Stack no admite `build`.
2. Copiar `.env.example` en **Environment** y completar `DATABASE_URL` y
   `TAIA_JWT_SECRET`. Usar `postgresql+psycopg://usuario:password@host:5432/taia`,
   con usuario/password codificados para URL cuando tengan caracteres especiales.
   Las variables de Gemini y Telegram son opcionales; habilitan esas integraciones.
   El Compose pasa estas variables explícitamente al contenedor.
3. Configurar **Domains** para el servicio `backend`, puerto `8000`, ruta `/`,
   con el dominio de la API y HTTPS. Dokploy agrega la configuración de Traefik
   y su red al servicio. Apuntar el DNS del dominio al servidor de Dokploy.
   No se publica el puerto 8000 directamente en el host.
4. Si PostgreSQL también está en Dokploy, usar su **host interno**, mantener
   desactivado **Isolated Deployments** y comprobar que el Compose convertido
   y PostgreSQL comparten `dokploy-network`. La configuración de Domains del
   paso anterior conecta el backend a esa red. Si se usa una red personalizada,
   declararla como externa y conectarla al backend en el Compose.
   Para una base externa, usar su endpoint accesible y opciones TLS necesarias.
   `localhost` dentro del backend identifica al propio contenedor.
5. Desactivar **Auto Deploy** de Git si se usará el workflow CD descrito abajo,
   para que los pushes no generen despliegues duplicados antes de terminar CI.
6. Pulsar **Deploy**. Revisar la ejecución de migraciones, los logs y el estado
   healthy del servicio. Consultar `https://TU_DOMINIO/health` y `/docs`.

El repositorio no requiere claves SSH, una IP fija de Oracle, un archivo
`~/taia.env` ni una imagen TAIA publicada en GHCR para desplegar.
El `.env` local y `backend/.env` quedan fuera del contexto de construcción.

## Despliegue después de CI

El workflow `.github/workflows/cd.yml` llama a `POST /api/compose.deploy` cuando
CI termina correctamente para un push a `main` del propio repositorio. Ignora
ejecuciones antiguas cuando la rama ya avanzó. Dokploy clona el código,
construye la imagen y administra el contenedor.

Configurar estos **GitHub Actions secrets**:

| Secret | Valor |
| --- | --- |
| `DOKPLOY_URL` | URL HTTPS de la instancia, por ejemplo `https://dokploy.example.com`, sin `/api`. |
| `DOKPLOY_API_KEY` | Token creado en el perfil de Dokploy con acceso al servicio. |
| `DOKPLOY_COMPOSE_ID` | ID del servicio Compose, visible en su URL o en la respuesta de `/api/project.all`. |

`OCI_HOST`, `OCI_USER`, `OCI_SSH_KEY`, `GHCR_USERNAME` y `GHCR_PAT` ya no se usan
en los workflows. Se pueden retirar de los secrets del repositorio después
de comprobar que ninguna otra integración los necesita.

Un CD verde indica que Dokploy **aceptó la solicitud**, no que el despliegue
terminó. Consultar el resultado en **Deployments**, los logs y el health check.
La API despliega la rama configurada en Dokploy; el SHA del título sirve para
trazabilidad, no fija la revisión. Si `main` cambia entre la comprobación del
workflow y el clone, Dokploy puede obtener el commit más reciente. Proteger
`main` con CI obligatorio antes de integrar cambios.

## Ejecutar con Compose localmente

Desde la raíz, copiar `.env.example` a `.env` (en PowerShell:
`Copy-Item .env.example .env`) y completar las variables. Este Compose no crea
PostgreSQL: usar una base accesible desde Docker. En Docker Desktop, una base
del equipo anfitrión normalmente se alcanza mediante `host.docker.internal`.

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build -d
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
docker compose -f docker-compose.yml -f docker-compose.local.yml logs -f backend
```

La API queda disponible en `http://127.0.0.1:8000/docs`. `TAIA_PORT` permite
cambiar el puerto local. Para detenerla:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down
```

## Migración desde el despliegue anterior

Configurar en Dokploy la conexión a la base existente y los secretos vigentes.
Conservar `TAIA_JWT_SECRET` si se desea mantener la validez de los tokens emitidos.
Crear una base nueva no traslada los datos: una migración de datos requiere
respaldo y restauración aparte. Respaldar la base antes de aplicar migraciones.

Validar el nuevo servicio antes de actualizar los clientes al dominio HTTPS y
retirar el contenedor anterior mediante la administración del servidor. El
repositorio ya no lo detiene por SSH. Los archivos `terraform/` siguen siendo
opcionales para administrar la infraestructura OCI por su API; no participan
en el despliegue de la aplicación ni instalan Dokploy.

## Referencias

- [Docker Compose y variables en Dokploy](https://docs.dokploy.com/docs/core/docker-compose).
- [Domains y redes](https://docs.dokploy.com/docs/core/docker-compose/domains).
- [API de Compose](https://docs.dokploy.com/docs/api/compose).
- [Despliegue automatizado y API keys](https://docs.dokploy.com/docs/core/auto-deploy).
