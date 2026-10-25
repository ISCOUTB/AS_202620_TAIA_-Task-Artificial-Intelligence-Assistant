# ADR-0010 — Plataforma de despliegue de la API: Dokploy con Docker Compose

## Estado

Aceptado el 2026-10-18, confirmado por el responsable del proyecto y recogido en
la configuración versionada. **Reemplaza a [ADR-0003](0003-plataforma-despliegue-api.md)**
(VM de OCI con Docker, GHCR y SSH), que se conserva sin cambios como antecedente.

Este contenido se registró primero como una reescritura de ADR-0003 (commit
`834415a`). Se movió a este ADR el 2026-10-25 para no modificar una decisión
aceptada.

## Contexto

La API de TAIA es una única aplicación FastAPI que debe estar accesible para
sus clientes y el evaluador. Mantiene el monolito modular de
[ADR-0001](0001-estilo-arquitectonico.md) y
[ADR-0008](0008-mantener-monolito-sin-extraer-modulos.md).

El despliegue anterior construía imágenes TAIA, las publicaba en GHCR y
reemplazaba un contenedor por SSH en una VM de OCI. Actualmente el repositorio
utiliza [Docker Compose](../../docker-compose.yml) y Dokploy para construir y
administrar el servicio. GitHub Actions ejecuta CI y solicita el despliegue
mediante un webhook.

Dokploy administra la aplicación sobre un servidor; puede utilizarse sobre
infraestructura OCI. Esta decisión no determina el tipo de VM ni sustituye
la decisión de base de datos de [ADR-0004](0004-plataforma-base-de-datos.md).
El destino PostgreSQL se configura mediante `DATABASE_URL`.

## Escenarios de calidad relacionados

- **S3 — Respuesta del asistente:** p95 ≤ 7 s.
- **RNF-08:** operaciones CRUD con p95 < 500 ms.
- **RNF-04:** comunicación cifrada en el despliegue.
- **RNF-06:** persistencia de los datos entre reinicios y despliegues.

La plataforma permite operar y observar el servicio; su adopción no demuestra
por sí sola el cumplimiento de estos requisitos. Los umbrales deben verificarse
en el entorno desplegado.

## Opciones consideradas

| Opción | Antecedente o motivo de elección |
|---|---|
| Docker directo en una VM de OCI | Decisión anterior, [ADR-0003](0003-plataforma-despliegue-api.md). Requería publicar la imagen en GHCR, administrar secretos en `~/taia.env` y reemplazar el contenedor por SSH. |
| Render Web Service Free | Alternativa descartada en ADR-0003. El arranque tras inactividad observado el 27/09/2026 tardó unos 53 s y motivó descartarla como entorno principal. La evidencia histórica no acredita un respaldo activo actualmente. |
| Dokploy con Docker Compose | Plataforma utilizada actualmente. Reúne la construcción desde Git, el entorno de ejecución, los despliegues, logs y dominios del servicio, conservando Compose y Dockerfile en el repositorio. |

La [comparación del taller](../taller_despliegue/) conserva las mediciones y
condiciones de septiembre de 2026. Los precios y cuotas allí registrados
corresponden a esa evaluación.

## Decisión

Desplegar la API como el servicio **`backend` de Docker Compose administrado
por Dokploy**, con el repositorio Git, rama `main` y Compose Path
`./docker-compose.yml`.

1. Construir la imagen desde la raíz con
   [`backend/Dockerfile`](../../backend/Dockerfile). El arranque aplica
   `alembic upgrade head` antes de iniciar Uvicorn en el puerto interno 8000.
2. Guardar las variables de aplicación en **Environment** de Dokploy.
   `env_file: .env` las carga en el contenedor. `DATABASE_URL`,
   `TAIA_JWT_SECRET` y `GEMINI_API_KEY` son necesarias para ejecutar el servicio;
   PostgreSQL debe existir y ser accesible antes del arranque.
3. Administrar el dominio y TLS en **Domains** de Dokploy para `backend:8000`.
   El Compose versionado expone el puerto interno sin publicarlo en el host.
4. Ejecutar [CI](../../.github/workflows/ci.yml) y solicitar el despliegue con
   [CD](../../.github/workflows/cd.yml) mediante `DOKPLOY_WEBHOOK_URL` cuando
   finaliza correctamente el CI de un push a `main` del propio repositorio y
   el SHA probado sigue siendo el último de la rama.
5. Verificar el resultado en **Deployments**, los logs y `/health`. El CD
   actual solo envía la solicitud; no espera la construcción ni comprueba
   que la nueva versión esté disponible.

La configuración de Environment y el modo Compose corresponden al mecanismo
[documentado por Dokploy](https://docs.dokploy.com/docs/core/docker-compose).
La configuración de Terraform que describía la VM de OCI de ADR-0003 se retiró
del repositorio el 2026-10-25: no participaba en el despliegue con Dokploy.

## Consecuencias

### Positivas

- Compose y Dockerfile mantienen versionados la construcción, el arranque,
  la política de reinicio y el health check del servicio.
- Dokploy centraliza la configuración y operación de la aplicación.
- Los secretos de aplicación se administran en Environment y no se transfieren
  por el workflow CD. GitHub Actions utiliza `DOKPLOY_WEBHOOK_URL` para el disparo.
- Se conserva una única unidad desplegable con persistencia PostgreSQL y las
  fronteras del monolito modular.

### Límites y obligaciones operativas

- El webhook y su configuración deben verificarse en la instancia instalada.
  El POST actual no transmite cuerpo, datos de rama ni SHA; un CD verde no
  demuestra que Dokploy haya iniciado o terminado el despliegue. La
  [documentación de webhooks](https://docs.dokploy.com/docs/core/auto-deploy)
  requiere Auto Deploy y coincidencia de rama para fuentes Git.
- CI construye una imagen de prueba sin publicarla; Dokploy vuelve a construir
  desde Git. Si la rama avanza entre la comprobación de CD y la descarga, puede
  obtener una revisión distinta de la probada.
- Para recuperar una versión anterior se puede revertir el cambio en Git,
  validarlo mediante CI y desplegar la reversión. Antes debe comprobarse su
  compatibilidad con las migraciones aplicadas: revertir código no restaura datos.
- La URL registrada en el repositorio utiliza HTTP. Configurar y comprobar
  HTTPS sigue siendo necesario para RNF-04; este documento no acredita su activación.
- El servidor de Dokploy, PostgreSQL, respaldos y proveedores externos requieren
  operación y presupuesto. Los **39,42 USD/mes** de
  [la estimación anterior](../costo_mensual.md) corresponden a la VM E5.Flex
  evaluada; usar Dokploy no confirma ni elimina ese costo. La facturación
  actual y el cumplimiento de la restricción de costo cero deben verificarse.
