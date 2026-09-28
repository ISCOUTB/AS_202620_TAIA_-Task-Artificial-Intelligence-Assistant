# ADR-0004 — Plataforma de la base de datos: Supabase PostgreSQL

## Estado

Aceptado.

## Contexto

TAIA persiste toda su información en PostgreSQL, con migraciones de Alembic (RNF-06). La API aplica las migraciones al arrancar (`alembic upgrade head` en `backend/Dockerfile`) y se conecta mediante `DATABASE_URL`, que llega desde los secretos de GitHub Actions. La restricción de costo de [arc42 §2](../arc42/02-restricciones-de-arquitectura.md) pide operar dentro de capas gratuitas.

La base de datos es una pieza separada de la API: la misma base sirvió a las dos alternativas del taller (ADR-0003).

## Escenario de calidad relacionado

**S4 — Acceso únicamente a datos del propio estudiante** y RNF-06: los datos tienen que sobrevivir a los reinicios y a los redespliegues del contenedor, que ocurren en cada push a `main`. También RNF-08 (CRUD con p95 < 500 ms), porque cada operación CRUD consulta la base.

## Opciones consideradas

### Opción A — Supabase PostgreSQL, plan Free

PostgreSQL administrado, con copias de seguridad y conexión por *pooler*.

Capa gratuita verificada ([Supabase Pricing](https://supabase.com/pricing)): 500 MB de base de datos, 5 GB de salida por mes, 2 proyectos activos, y el proyecto se pausa tras 1 semana de inactividad. No pide tarjeta.

### Opción B — PostgreSQL en un contenedor dentro de la VM de OCI

Sin proveedor adicional y sin latencia de red externa, pero el equipo tendría que gestionar el volumen de datos, las copias de seguridad y las actualizaciones, y la base se perdería si se recrea la VM. Tampoco reduce el costo: la VM ya se paga por hora (ver [costo_mensual.md](../costo_mensual.md)).

### Opción C — Render Postgres Free

Capa gratuita verificada ([Render Free](https://render.com/docs/free)): 1 GB de almacenamiento, pero **la base expira 30 días después de crearla**, lo cual no alcanza para un semestre.

## Decisión

La base de datos de TAIA es **Supabase PostgreSQL en el plan Free**, en la región `us-west-2`, con conexión por el *pooler* de Supabase.

Se descarta **PostgreSQL dentro de la VM** porque pone la durabilidad de los datos en manos de una sola VM sin copias de seguridad y suma operación al equipo. Se descarta **Render Postgres Free** porque expira a los 30 días.

## Consecuencias

### Positivas

- Costo de 0 USD con el volumen supuesto: 150 MB por semestre y 0,75 GB de salida al mes, frente a 500 MB y 5 GB.
- Los datos no dependen de la VM: se puede recrear o cambiar la plataforma de la API (ADR-0003) sin migrar datos.
- Las migraciones de Alembic funcionan igual que en local y en CI, porque es PostgreSQL estándar.

### Negativas

- El tamaño se rompe con unos 330 estudiantes activos durante un semestre (ver [costo_mensual.md](../costo_mensual.md)).
- Si la base pasa una semana sin actividad, Supabase pausa el proyecto y la API falla hasta que alguien lo reactive desde el panel.
- Cada consulta cruza la red entre OCI y Supabase, lo cual suma latencia a RNF-08. La medición real se ve en `GET /metrics`.
