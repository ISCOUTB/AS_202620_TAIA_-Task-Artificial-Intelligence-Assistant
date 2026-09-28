# ADR-0003 — Plataforma de despliegue de la API: VM de OCI con Docker

## Estado

Aceptado.

## Contexto

La API de TAIA (FastAPI, un solo proceso, ver ADR-0001) tiene que estar accesible desde Internet para el cliente y el evaluador. Se despliega como una imagen Docker construida desde `backend/Dockerfile`. La restricción de costo de [arc42 §2](../arc42/02-restricciones-de-arquitectura.md) pide operar dentro de capas gratuitas.

En el taller de despliegue ([comparación de alternativas](../taller_despliegue/)) se probaron dos plataformas con la misma imagen y la misma base de datos en Supabase (ver ADR-0004).

## Escenario de calidad relacionado

**S3 — Respuesta del asistente ante un mensaje** (p95 ≤ 7 s) y RNF-08 (CRUD con p95 < 500 ms). La restricción del escenario es el hosting gratuito sin recursos dedicados: un arranque en frío de un minuto rompe la medida por sí solo. La latencia se consulta en `GET /metrics`.

## Opciones consideradas

### Opción A — VM de Oracle Cloud Infrastructure con Docker

Una VM propia en OCI ejecuta el contenedor con `docker run --restart unless-stopped`. El workflow `cd.yml` publica la imagen en GitHub Container Registry y la despliega por SSH cuando el CI termina en verde sobre `main`. La VM se describe en Terraform (`terraform/`).

Capa gratuita verificada ([Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)): solo `VM.Standard.E2.1.Micro` (1/8 OCPU, 1 GB, hasta 2) y `VM.Standard.A1.Flex` (ARM, 2 OCPU y 12 GB en total). Al crear la VM, la A1.Flex no tenía capacidad disponible y la consola no ofrece cambiar a la E2.1.Micro, así que la VM quedó en `VM.Standard.E5.Flex` (1 OCPU, 12 GB), que **no es Always Free**. OCI exige tarjeta para crear la cuenta.

### Opción B — Render Web Service Free

Servicio administrado que toma la misma imagen de GHCR, con HTTPS incluido y sin tarjeta.

Capa gratuita verificada ([Render Free](https://render.com/docs/free)): 750 horas de instancia por mes y workspace, y el servicio se suspende tras 15 minutos sin tráfico. En el taller, la primera petición después de la inactividad tardó cerca de un minuto (53 s medidos el 27/09/2026).

## Decisión

La API se despliega en una **VM de OCI (`VM.Standard.E5.Flex`, 1 OCPU, 12 GB) con Docker**, con la imagen publicada en **GitHub Container Registry** y desplegada automáticamente por `cd.yml`.

URL pública: `http://157.137.215.57:8000` (health check en `/health`).

Se descarta **Render Free** como entorno principal: la suspensión por inactividad hace que la primera petición tarde cerca de un minuto, lo cual incumple S3 y RNF-08 cada vez que el servicio lleva 15 minutos sin tráfico. Además, no permite SSH ni controlar el contenedor. Sigue desplegado en `https://taia-backend-latest.onrender.com` como alternativa de respaldo sin costo.

## Consecuencias

### Positivas

- El proceso no se suspende: no hay arranques en frío y la latencia medida en `/metrics` refleja la operación real.
- El despliegue es automático y trazable: cada imagen lleva el SHA del commit como etiqueta, y el rollback consiste en volver a ejecutar el contenedor con una etiqueta anterior.
- Los secretos llegan desde GitHub Actions a `~/taia.env` en la VM y no quedan en el repositorio ni en la imagen.

### Negativas

- **Costo: 39,42 USD/mes** a precio de lista (ver [costo_mensual.md](../costo_mensual.md)). Rompe la restricción de costo cero y está registrado como riesgo en arc42 §11.
- No hay HTTPS: la API se expone por HTTP en el puerto 8000, lo cual incumple RNF-04 hasta que se configure un dominio y un proxy con TLS.
- El equipo administra el sistema operativo, Docker y la red. Terraform todavía no describe la VCN ni las reglas de seguridad.
- Pasar a A1.Flex (Always Free) cuando haya capacidad exige construir la imagen también para ARM64.
