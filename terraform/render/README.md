# TAIA en Render

GitHub Actions ejecuta pruebas del backend con PostgreSQL, comprueba el cliente
generado, construye y arranca Docker, y valida Terraform. Render construye desde
GitHub y despliega la rama configurada cuando pasan los checks. Ya no se publica
la imagen de TAIA en GHCR ni se ejecuta SSH desde Actions.

## Configuración

| Campo | Valor |
| --- | --- |
| Recurso | `render_web_service.taia` |
| Runtime | Docker |
| Dockerfile | `backend/Dockerfile` |
| Contexto | Raíz del repositorio (`.`); no configurar `backend` como Root Directory |
| Rama | `main`; configurable para validar `migrate_to_render` |
| Auto deploy | `checksPass` / After CI Checks Pass |
| Health check | `/health` |
| Puerto | `0.0.0.0:$PORT`, con fallback local `8000` |
| Réplicas | 1; Alembic se ejecuta antes de iniciar Uvicorn |
| Base de datos | PostgreSQL existente, fuera de este estado de Terraform |

El plan de ejemplo es `starter` (de pago). Elegir plan y región antes de aplicar.
Esta configuración no crea ni restaura PostgreSQL. Si se migra a Render Postgres,
hacer el respaldo y la restauración por separado y proporcionar su URL.

## Preparar Render y los secretos

1. Conectar la cuenta de GitHub con Render y conceder acceso al repositorio de TAIA.
   La integración Git es necesaria para auto deploy; una URL pública sin conexión
   no basta. Subir la rama con el Dockerfile y CI nuevos antes del primer despliegue.
2. Obtener una API key y el owner ID del workspace de Render. Proporcionarlos al
   proceso de Terraform como `RENDER_API_KEY` y `RENDER_OWNER_ID`. No hacen falta
   secretos de Render en GitHub Actions: CI no ejecuta `plan` ni `apply`.
3. Copiar `terraform.tfvars.example` a `terraform.tfvars` **dentro de esta carpeta**,
   sin sobrescribir una copia existente. Configurar rama, nombre, región y plan.
4. Cargar los secretos del backend desde el gestor de secretos o entorno local:

| Variable de Terraform | Variable en Render | Uso |
| --- | --- | --- |
| `TF_VAR_database_url` | `DATABASE_URL` | Obligatoria; PostgreSQL accesible desde Render |
| `TF_VAR_jwt_secret` | `TAIA_JWT_SECRET` | Obligatoria; secreto de producción, mínimo 32 caracteres |
| `TF_VAR_additional_environment_variables` | Mapa JSON de variables adicionales | Opcional; ver abajo |

El mapa adicional admite `GEMINI_API_KEY`, `GEMINI_MODEL`,
`TAIA_TELEGRAM_BOT_TOKEN` y `TAIA_TELEGRAM_BOT_USERNAME`. Los nombres coinciden
con los que lee el backend. No puede sustituir `DATABASE_URL` ni `TAIA_JWT_SECRET`.
Render proporciona `PORT`; no hace falta configurarla manualmente.

Conservar el secreto JWT de OCI para mantener válidas las sesiones. Si el anterior
era el valor de desarrollo o no satisface el mínimo, rotarlo y prever nuevos logins.
`DATABASE_URL` debe comenzar con `postgresql://` o `postgresql+psycopg://`.
Usar la URL entregada por el proveedor; si empieza con el alias `postgres://`,
adaptar únicamente ese prefijo a `postgresql://`. Mantener sus opciones de TLS.
Una dirección `localhost` o una IP privada de OCI no será accesible desde Render:
verificar red, firewall y conectividad antes del cambio.

Terraform configura estas variables en Service → Environment. Sus cambios se
administran mediante Terraform; una edición manual en Render puede ser revertida
en el siguiente apply. Aunque estén marcadas `sensitive`, **sus valores quedan en
el estado y en los planes guardados**. Protegerlos y mantenerlos fuera de Git;
también puede haber secretos al importar un servicio existente. No versionar
`taia.env`, `.env`, estados ni planes. Antes de trabajar entre varias personas,
configurar un backend de estado compartido con acceso restringido y bloqueo.

## Validar y crear el servicio

Desde la raíz del repositorio:

```bash
terraform -chdir=terraform/render init
terraform -chdir=terraform/render fmt -check
terraform -chdir=terraform/render validate
terraform -chdir=terraform/render plan -out=review.tfplan
# Revisar: solo debe crear el Web Service de Render; no debe cambiar OCI.
terraform -chdir=terraform/render apply review.tfplan
terraform -chdir=terraform/render output
```

Se versiona el lockfile del provider `render-oss/render` 1.9.1. CI inicializa con
`-lockfile=readonly` y no necesita credenciales de producción. El directorio
`terraform/` conserva la configuración y estado de OCI: **no copiar ni migrar ese
estado a esta carpeta**. No hay un módulo que combine ambos proveedores.

Si el Web Service ya existe, importarlo antes del primer plan para evitar duplicados:

```bash
terraform -chdir=terraform/render import render_web_service.taia srv_REEMPLAZAR
terraform -chdir=terraform/render plan
```

Alinear variables con el servicio importado y revisar cualquier diferencia.
`prevent_destroy` bloquea reemplazos mientras el recurso siga declarado.
La creación del servicio inicia un despliegue: comprobar previamente el CI de ese
commit. Los cambios posteriores de infraestructura no provocan un despliegue
desde el provider (`skip_deploy_after_service_update = true`); tras revisar CI,
desplegar manualmente para activar cambios de configuración. El auto deploy de
nuevos commits queda a cargo de Render.

## Validación y cambio de tráfico

1. Respaldar PostgreSQL antes del primer arranque: el Dockerfile ejecuta
   `alembic upgrade head`. Validar que las migraciones sean compatibles con OCI
   mientras ambos backends compartan la base de datos. No escalar réplicas sin
   separar o serializar primero la ejecución de migraciones.
2. Revisar en Render el SHA desplegado, build, logs de Alembic, inicio de Uvicorn
   y estado Live. Comparar el SHA con el commit validado por GitHub Actions.
3. Consultar las URLs de `terraform output`:

   ```bash
   curl --fail --show-error https://SERVICIO.onrender.com/health
   curl --fail --show-error https://SERVICIO.onrender.com/docs
   ```

4. Probar registro/login y lectura/escritura de tareas con una cuenta de prueba.
   `/health` devuelve `{"status":"ok"}` pero no consulta PostgreSQL; por sí solo
   no demuestra que los datos estén disponibles. Comprobar también Gemini y
   Telegram cuando esas integraciones estén habilitadas.
5. Probar un push controlado en la rama desplegada: esperar los tres jobs de CI,
   el despliegue automático de Render y comprobar el nuevo SHA y los endpoints.
   Al fallar un check no debe iniciarse el auto deploy. No configurar además un
   deploy hook: produciría un segundo mecanismo de despliegue.
6. Actualizar la URL del backend en frontend, bot e integraciones a HTTPS de Render.
   Si se validó sobre `migrate_to_render`, cambiar la variable `branch` a `main`
   después de integrar los cambios y validar su CI.

## Datos y rollback

Si se mantiene PostgreSQL, conservar los datos y ajustar solamente conectividad
y `DATABASE_URL`. Si se cambia de base de datos, hacer un respaldo con `pg_dump`,
restaurarlo en una base vacía y comprobar esquema, conteos y operaciones. Detener
las escrituras durante la copia final para evitar divergencia entre ambas bases.

Mantener el contenedor y la VM de OCI disponibles durante la observación. Para
rollback, devolver los clientes a la URL anterior y detener las escrituras en
Render si las bases son distintas. Reconciliar los datos escritos desde el cambio
antes de reabrir OCI. Un rollback de aplicación no revierte las migraciones de
Alembic: confirmar la compatibilidad del esquema con el backend anterior.

El workflow de CD a OCI se elimina en esta rama. Los secretos `OCI_HOST`,
`OCI_USER`, `OCI_SSH_KEY`, `GHCR_USERNAME` y `GHCR_PAT` dejan de ser necesarios
para este pipeline; retirarlos de GitHub cuando se confirme que otros procesos no
los usan. Conservar el acceso operativo a OCI durante el rollback. No borrar
imágenes antiguas ni apagar/eliminar la VM hasta validar Render, datos e
integraciones y completar el período de observación.

## Referencias

- [Provider oficial de Render](https://registry.terraform.io/providers/render-oss/render/1.9.1/docs).
- [Web Service y esquema Docker](https://registry.terraform.io/providers/render-oss/render/1.9.1/docs/resources/web_service).
- [Auto deploy después de CI](https://render.com/docs/deploys#integrating-with-ci).
