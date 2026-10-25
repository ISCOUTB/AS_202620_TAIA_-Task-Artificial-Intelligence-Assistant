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
   `TAIA_JWT_SECRET` y `GEMINI_API_KEY`. Obtener la conexión de PostgreSQL del
   proveedor y guardarla únicamente en Environment; codificar sus credenciales
   para URL cuando tengan caracteres especiales.
   Gemini es obligatorio al arrancar; Telegram es opcional.
   Dokploy guarda Environment en `.env`, junto a `docker-compose.yml`.
   Compose carga ese archivo mediante `env_file: .env` y pasa sus variables
   al entorno del contenedor; el backend las lee con `os.getenv`.
   `DATABASE_URL` y `TAIA_JWT_SECRET` conservan la validación obligatoria.
   No es necesario copiar ni montar `.env` dentro de la imagen.
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
5. Mantener activado **Auto Deploy**: el webhook de despliegue lo requiere y
   solo se acepta para la rama configurada
   ([documentación de webhooks](https://docs.dokploy.com/docs/core/auto-deploy)).
   Copiar la **Webhook URL** del servicio y guardarla como secret de GitHub
   (ver abajo). No registrarla en *Settings → Webhooks* del repositorio: solo
   `cd.yml` debe llamarla, para que ningún push despliegue antes de que
   termine el CI.
6. Pulsar **Deploy**. Revisar la ejecución de migraciones, los logs y el estado
   healthy del servicio. Consultar `https://taia-sistema.iscoutb.dev/health`
   y `https://taia-sistema.iscoutb.dev/docs`.

El repositorio no requiere claves SSH, una IP fija de Oracle, un archivo
`~/taia.env` ni una imagen TAIA publicada en GHCR para desplegar.
El `.env` local y `backend/.env` quedan fuera del contexto de construcción.

## Despliegue después de CI

El workflow `.github/workflows/cd.yml` envía un `POST` a la Webhook URL del
servicio en Dokploy cuando CI termina correctamente para un push a `main` del
propio repositorio. Antes comprueba que el SHA probado siga siendo el último de
`main` e ignora las ejecuciones antiguas. Dokploy clona el código, construye la
imagen y administra el contenedor.

Configurar este **GitHub Actions secret**:

| Secret | Valor |
| --- | --- |
| `DOKPLOY_WEBHOOK_URL` | Webhook URL del servicio Compose, copiada de su pestaña de despliegues en Dokploy. Debe usar HTTPS; con HTTP el workflow solo emite una advertencia. |

El `POST` no lleva cuerpo ni credenciales adicionales: quien conoce la URL puede
disparar un despliegue, por eso se guarda únicamente como secret.

`OCI_HOST`, `OCI_USER`, `OCI_SSH_KEY`, `GHCR_USERNAME` y `GHCR_PAT` ya no se usan
en los workflows. Se pueden retirar de los secrets del repositorio después
de comprobar que ninguna otra integración los necesita.

Un CD verde indica que Dokploy **aceptó la solicitud**, no que el despliegue
terminó. Consultar el resultado en **Deployments**, los logs y el health check.
Dokploy despliega la rama configurada; el webhook no transmite el SHA, así que
no fija la revisión. Si `main` cambia entre la comprobación del workflow y el
clone, Dokploy puede obtener el commit más reciente. Proteger
`main` con CI obligatorio antes de integrar cambios.

El servicio actualmente desplegado está disponible en
`https://taia-sistema.iscoutb.dev`, con documentación
interactiva en `/docs` y health check en `/health`.

## Ejecutar con Compose localmente

Desde la raíz, copiar `.env.example` a `.env` (en PowerShell:
`Copy-Item .env.example .env`) y completar las variables. Este Compose no crea
PostgreSQL: usar una base accesible desde Docker. En Docker Desktop, una base
del equipo anfitrión normalmente se alcanza mediante `host.docker.internal`.

`docker-compose.yml` solo expone el puerto 8000 dentro de la red de Docker,
porque en Dokploy lo publica Traefik. Para usarlo en local, crear en la raíz un
`docker-compose.local.yml` que publique el puerto. El archivo está en
`.gitignore`: cada desarrollador mantiene el suyo y no se versiona.

```yaml
services:
  backend:
    ports:
      - "127.0.0.1:${TAIA_PORT:-8000}:8000"
    # En Linux, host.docker.internal no existe por defecto.
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

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
repositorio ya no lo detiene por SSH. La configuración de Terraform de la VM
de OCI se retiró del repositorio porque no participaba en el despliegue de la
aplicación ni instalaba Dokploy.

## Referencias

- [Docker Compose y variables en Dokploy](https://docs.dokploy.com/docs/core/docker-compose).
- [Domains y redes](https://docs.dokploy.com/docs/core/docker-compose/domains).
- [Auto Deploy y Webhook URL](https://docs.dokploy.com/docs/core/auto-deploy).
