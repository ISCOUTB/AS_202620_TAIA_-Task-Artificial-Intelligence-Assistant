# ADR-0009 — Una base PostgreSQL compartida con referencias lógicas entre módulos

## Estado

Aceptado por el equipo el 2026-10-25. Registra una decisión que ya estaba aplicada desde las
migraciones `0001` a `0004` y en las convenciones de [diccionario_datos.md](../diccionario_datos.md),
pero que no tenía un ADR propio.

## Contexto

TAIA tiene cuatro módulos (`usuario`, `academic`, `reminders`, `ai`), cada uno propietario de sus
tablas ([arc42 §8.4](../arc42/08-conceptos-transversales.md#84-propiedad-de-datos),
[propiedad_datos_s6.md](../propiedad_datos_s6.md)). [ADR-0004](0004-plataforma-base-de-datos.md)
eligió **dónde** vive la base (Supabase PostgreSQL); este ADR registra **cómo se reparten los datos
de los módulos dentro de ella**.

Estado actual, verificado sobre el código:

| Hecho | Evidencia |
|---|---|
| Las 19 tablas de los cuatro módulos están en una sola base y en el esquema `public`. | [`backend/alembic/versions/`](../../backend/alembic/versions/), [diccionario_datos.md, §3](../diccionario_datos.md) |
| Hay un único historial de Alembic (`0001` → `0004`) para todos los módulos. | `down_revision` de cada migración |
| Dentro de un módulo las relaciones usan `FOREIGN KEY`; entre módulos, una columna `uuid` sin `FOREIGN KEY` (**referencia lógica**). | [diccionario_datos.md, §1](../diccionario_datos.md); `reminders.user_id` y `reminders.task_id` son `Uuid` sin `ForeignKey` en [`reminders/.../sqlalchemy_models.py:28-29`](../../backend/app/modules/reminders/adapters/outbound/sqlalchemy_models.py) |
| La existencia y pertenencia de una referencia lógica la valida el módulo propietario mediante su puerto. | `AcademicTaskLookup` en [`create_reminder.py:22-23`](../../backend/app/modules/reminders/application/use_cases/create_reminder.py), `IdentityService` |
| Usuarios, tareas y asignaturas con actividades no se eliminan físicamente (RT-04), así que una referencia lógica no queda huérfana. | [diccionario_datos.md, §1, eliminación](../diccionario_datos.md) |

Entre todas las decisiones de datos de TAIA (tipos `uuid`, `timestamptz` en UTC, borrado lógico,
`ENUM` nativos), esta es **la más costosa de revertir**: fija qué consultas pueden cruzar módulos, qué
transacciones son locales y cuánto trabajo cuesta extraer un módulo
([ADR-0008](0008-mantener-monolito-sin-extraer-modulos.md)). Cambiar un tipo de columna es una
migración; cambiar el reparto de los datos entre módulos toca el esquema, el código de los adaptadores,
las pruebas y el despliegue a la vez.

## Escenarios de calidad relacionados

- **S1 — Registro correcto de información académica:** una escritura que cruza módulos no debe quedar
  a medias.
- **S4 — Acceso únicamente a datos del propio estudiante:** todas las tablas filtran por `user_id`.
- **RNF-06 — Persistencia y migraciones con Alembic.**
- **RNF-08 — CRUD con p95 < 500 ms:** cada salto de red o consulta adicional suma latencia.

## Criterios de decisión

| Criterio | Pregunta |
|---|---|
| Integridad | ¿Quién garantiza que una referencia entre módulos apunte a algo que existe? |
| Acoplamiento | ¿Un cambio de esquema en un módulo obliga a cambiar otro? |
| Transacciones | ¿Las escrituras de cada operación siguen siendo locales? |
| Extracción | ¿Cuánto cuesta separar un módulo en su propio servicio si se cumple un disparador de ADR-0008? |
| Costo y operación | ¿Cuántas bases, conexiones, migraciones y copias hay que mantener? La capa gratuita de Supabase permite 2 proyectos activos y 500 MB ([ADR-0004](0004-plataforma-base-de-datos.md)). |

## Opciones consideradas

### Opción A — Una base y un esquema, con referencias lógicas entre módulos (actual)

- **Integridad:** dentro del módulo la impone PostgreSQL; entre módulos la impone el puerto del
  propietario, apoyado en el borrado lógico (RT-04).
- **Acoplamiento:** ningún módulo declara `FOREIGN KEY` hacia tablas de otro, de modo que puede
  cambiar sus tablas sin romper restricciones ajenas.
- **Transacciones:** cada escritura es local de un módulo ([arc42 §8.10](../arc42/08-conceptos-transversales.md#810-consistencia-de-los-datos)).
- **Extracción:** las tablas de un módulo se pueden copiar a otra base sin desmontar claves foráneas.
- **Costo y operación:** una conexión (`DATABASE_URL`), un historial de Alembic, un proyecto de Supabase.
- **En contra:** la base no detecta una referencia lógica inválida si alguien escribe sin pasar por el
  puerto; y nada en PostgreSQL impide que un adaptador consulte tablas ajenas: lo impiden las pruebas
  de frontera y la revisión.

### Opción B — Una base y un esquema, con `FOREIGN KEY` entre módulos

- **Integridad:** PostgreSQL garantiza que `reminders.task_id` exista en `tasks`.
- **Acoplamiento:** `reminders` queda atado a la tabla `tasks` de `academic`; renombrarla, partirla o
  moverla exige migrar también `reminders`. Es la dependencia que [arc42 §8.5](../arc42/08-conceptos-transversales.md#85-reglas-de-modularidad-y-comunicación-entre-contextos)
  prohíbe en el código.
- **Extracción:** antes de separar un módulo hay que eliminar sus claves foráneas y añadir la
  validación por puerto que la opción A ya tiene.
- **Ganancia real limitada:** como las tareas no se borran físicamente (RT-04), la clave foránea casi
  nunca rechazaría algo.

### Opción C — Un esquema PostgreSQL por módulo en la misma base

- **Acoplamiento:** igual que A, pero con la frontera visible en la base (`academic.tasks`,
  `reminders.reminders`) y permisos por esquema posibles.
- **Transacciones:** siguen siendo locales y en la misma base.
- **Costo:** mover las 19 tablas, ajustar `__table_args__` de todos los modelos, `search_path` y las
  migraciones. Aporta más sobre la opción A cuando hay varios equipos o roles de base de datos, que
  TAIA no tiene.
- Queda como paso intermedio razonable si se cumple un disparador de extracción.

### Opción D — Una base por módulo

- **Acoplamiento y extracción:** la máxima independencia.
- **Transacciones:** las consultas que hoy unen datos de un mismo módulo no cambian, pero toda
  validación entre módulos pasa a ser una llamada entre bases o servicios, y el plan de estudio
  (que valida contra horario y tareas) seguiría en una sola.
- **Costo y operación:** cuatro conexiones, cuatro historiales de Alembic y cuatro copias de
  seguridad. Supabase Free admite **2 proyectos activos**, así que no cabe en la capa gratuita.
- Sin un segundo servicio que la use, solo suma costo ([ADR-0008](0008-mantener-monolito-sin-extraer-modulos.md)).

## Decisión

Se adopta la **opción A**: una base PostgreSQL y un esquema, con propiedad de tablas por módulo,
`FOREIGN KEY` solo dentro de un módulo y **referencias lógicas** (`uuid` validado por el puerto del
propietario) entre módulos.

Es la opción que mantiene las transacciones locales y el costo de una sola base, sin atar el esquema
de un módulo al de otro. La integridad que pierde respecto a la opción B se compensa con el borrado
lógico y con la validación del propietario, y la frontera que pierde respecto a la opción C se
comprueba en las pruebas de frontera.

## Costo de reversión

| Cambio a otra opción | Qué hay que tocar | Costo relativo |
|---|---|---|
| A → B (añadir claves foráneas) | Una migración con `ALTER TABLE … ADD FOREIGN KEY` para `user_id` y `task_id` en `reminders`, `academic`, `ai`; limpiar antes las filas que no cumplan. | **Bajo**, pero empeora la extracción. |
| A → C (esquema por módulo) | Migración que mueve 19 tablas (`ALTER TABLE … SET SCHEMA`), `schema=` en todos los modelos SQLAlchemy, ajustes en Alembic (`version_table_schema`, `include_schemas`) y en las pruebas que crean y borran tablas. Sin cambios en el dominio ni en los puertos. | **Medio**: un cambio de infraestructura de todos los módulos a la vez, sin tocar el dominio. |
| A → D (base por módulo) | Todo lo de C, más cuatro `DATABASE_URL`, cuatro historiales de Alembic, migrar datos en producción con la API detenida, pasar las validaciones entre módulos a llamadas entre servicios, y un plan de costo fuera de la capa gratuita. | **Alto**: es la extracción de ADR-0008. |
| B o D → A (deshacer) | Desde B, eliminar claves foráneas (bajo). Desde D, volver a juntar bases y reconciliar datos duplicados o desfasados (alto). | — |

Partir de A deja el camino abierto en las tres direcciones con el menor costo hacia C y D, que son las
que pedirían los disparadores de ADR-0008. Partir de B habría hecho más cara cualquier extracción; partir
de D habría pagado desde el inicio un costo que hoy no tiene uso.

### Disparadores para revisar la decisión

1. Se cumple un disparador de [ADR-0008](0008-mantener-monolito-sin-extraer-modulos.md) y un módulo
   pasa a correr en otro proceso: primero se aplica la opción C para ese módulo.
2. Aparece una referencia lógica inválida en producción (por ejemplo, un recordatorio cuya tarea no
   existe), lo que indicaría una escritura que no pasó por el puerto.
3. Se introduce borrado físico de tareas o usuarios, que rompería el supuesto de RT-04.

## Consecuencias

### Positivas

- Las escrituras siguen siendo transacciones locales de un módulo.
- Ningún módulo puede romper el esquema de otro con una migración propia.
- Una sola base, una conexión y un historial de migraciones, dentro de la capa gratuita.
- Extraer un módulo no requiere desmontar claves foráneas.

### Negativas

- La integridad entre módulos depende del código (puertos y borrado lógico), no de la base.
- El esquema no muestra las fronteras: `reminders.task_id` parece una columna suelta si no se lee el
  diccionario.
- Un error en un adaptador podría consultar tablas ajenas; lo detectan las pruebas de frontera, no
  PostgreSQL.

## Trazabilidad

- **Requisitos:** `RNF-06` (Alembic), `RNF-08` (p95 CRUD), `RT-04` (borrado lógico), `RF-REC-01`
  (recordatorio asociado a una tarea).
- **Aspectos:** A-05 y A-06 de [aspectos.md](../aspectos.md).
- **C4:** [C4-C2](../c4/C4-C2.md), contenedor «Base de Datos» (PostgreSQL).
- **Datos:** [diccionario_datos.md, §1 y §3](../diccionario_datos.md),
  [propiedad_datos_s6.md](../propiedad_datos_s6.md).
- **Consistencia:** [arc42 §8.10](../arc42/08-conceptos-transversales.md#810-consistencia-de-los-datos).
- **Pruebas de frontera:** [`test_s8_closure.py`](../../backend/tests/test_s8_closure.py).
- **Implementación:** no requiere cambios de código; el commit que introduce este ADR es su registro.
