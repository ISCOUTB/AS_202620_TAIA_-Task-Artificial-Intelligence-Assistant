# ADR-0012 — Enviar los recordatorios con un proceso periódico dentro de la API

## Estado

Aceptado por el equipo el 2026-11-20. El equipo pidió a la IA que eligiera entre las opciones y
aceptó esta propuesta. Redactado con apoyo de IA.

Implementación: frente B del cierre S16 (RF-NOT-02).

## Contexto

RF-NOT-02 pide que un proceso del backend revise, al menos cada minuto, los recordatorios
`pending` cuya hora ya llegó y envíe la notificación. Hoy solo se envía cuando alguien llama a
`POST /reminders/{id}/notify`.

Las condiciones de partida son estas:

- La API corre como un solo contenedor en Dokploy, con `docker-compose.yml`
  ([ADR-0010](0010-despliegue-con-dokploy-y-docker-compose.md)) y un único proceso `uvicorn`
  (`backend/Dockerfile`).
- El diccionario ya define cómo se reclama un recordatorio sin duplicarlo:
  `UPDATE ... SET status = 'sent' WHERE id = :id AND status = 'pending'`
  ([diccionario_datos.md §7.1](../diccionario_datos.md)). Si la actualización no afecta ninguna
  fila, otro proceso ya lo tomó.

## Escenarios de calidad relacionados

- **RF-NOT-02:** un recordatorio de las 18:00 de Colombia sale entre las 18:00 y las 18:01, y dos
  ejecuciones seguidas envían una sola notificación.
- **RNF-09:** una caída de Firebase no impide usar el resto del sistema.
- **RT-03:** la comparación usa instantes con zona, no la hora del servidor.

## Opciones consideradas

| Opción | Ventaja | Costo |
|---|---|---|
| A. Tarea periódica en el `lifespan` de FastAPI | Sin dependencias ni contenedores nuevos; usa el mismo código y la misma configuración | Si la API está caída, no se envía nada hasta que vuelva |
| B. APScheduler dentro de la API | Planificación declarativa | Una dependencia nueva para algo que es un bucle de un minuto; el mismo problema de la opción A ante una caída |
| C. Worker o cron aparte en `docker-compose` | Separa el envío de las peticiones HTTP | Un segundo servicio que desplegar, vigilar y configurar en Dokploy, con los mismos secretos |

## Decisión

Se adopta la **opción A**.

1. **Bucle.** Al arrancar, el `lifespan` lanza una tarea `asyncio` que cada 60 segundos ejecuta
   el caso de uso `dispatch_due_reminders(now)` en un hilo (`asyncio.to_thread`), para no bloquear
   las peticiones. Al apagar, la tarea se cancela.
2. **Idempotencia.** La garantiza la base de datos, no el planificador: cada recordatorio se
   reclama con el `UPDATE` condicional del diccionario. Si en el futuro hay más de una réplica,
   tampoco se duplican los envíos.
3. **Errores.** Un fallo en una ejecución se registra en el log (sin datos del usuario, RNF-05) y
   no detiene el bucle. Los fallos de FCM siguen la política de reintentos de RF-NOT-02.
4. **Pruebas.** Las pruebas llaman al caso de uso con un reloj inyectado. El bucle no se ejecuta
   en la suite.

## Consecuencias

### Positivas

- No hay dependencias, servicios ni secretos nuevos.
- El envío usa los mismos puertos y la misma configuración que la API.

### Negativas

- Si la API está caída, los recordatorios vencidos salen cuando se recupera, tarde. Se envían
  igual en lugar de descartarse, porque un aviso tardío sigue siendo útil para una tarea pendiente.
- El envío comparte CPU y conexiones con las peticiones HTTP. Con la carga del MVP no es un
  problema medible.

### Puntos abiertos

- Si se despliega más de una réplica, cada una ejecuta el bucle. La idempotencia evita los
  duplicados, pero se hacen consultas de más. Ese día conviene revisar la opción C.

## Trazabilidad

| Eslabón | Referencia |
|---|---|
| Requisitos | RF-NOT-02, RF-NOT-04, RNF-09, RT-03 |
| Datos | `reminders` y `notifications` en [diccionario_datos.md §7](../diccionario_datos.md) |
| Elementos C4 | Componente Reminders ([C4-C3](../c4/C4-C3.md)) |
| ADR relacionados | [ADR-0010](0010-despliegue-con-dokploy-y-docker-compose.md) |
| Código y pruebas | Pendientes (frente B) |
