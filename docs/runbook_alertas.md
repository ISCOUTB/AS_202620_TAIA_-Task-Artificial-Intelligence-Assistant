# Runbook de alertas

Las alertas de T-14 se evalúan en
[`observability.py`](../backend/app/shared/adapters/inbound/observability.py) sobre la misma
ventana que alimenta `GET /metrics`. No hay un servicio externo de guardia: la alerta existe
para que el ataque o la falla deje rastro en los logs del contenedor y para que `/metrics`
muestre el estado sin tener que reconstruirlo a mano.

## Cómo funciona

- Cada petición registra método, ruta, estado y duración. Nunca el cuerpo, el token ni el
  mensaje del usuario (RNF-05).
- Los contadores de estado cubren los **últimos 15 minutos** por ruta. Al vencer un evento se
  descuenta, así que una alerta puede volver a la normalidad y limpiarse.
- La latencia p95 se calcula sobre las **últimas 1 000 peticiones** de cada ruta.
- Cuando una regla pasa de inactiva a activa se emite `alert_triggered` con nivel `WARNING`.
  Cuando vuelve a la normalidad se emite `alert_cleared` con nivel `INFO`. Solo se registran
  las transiciones, no cada petición que sigue incumpliendo.
- `GET /metrics` devuelve `routes` (peticiones, estados, p95, objetivo) y `alerts` (las reglas
  activas en este momento). Exige JWT (RT-01).

Ejemplo de línea en `docker logs`:

```json
{"timestamp":"2026-10-31T10:15:00.000-05:00","level":"WARNING","logger":"taia",
 "event":"alert_triggered","rule":"PROBE-404","severity":"warning",
 "route":"unmatched","value":57,"threshold":50,
 "message":"Sondeo de rutas: muchos 404 en la ventana"}
```

## Catálogo de alertas

| Regla | Severidad | Dispara cuando | Qué significa | Primer paso |
|---|---|---|---|---|
| `AUTH-401` | crítica | 20 o más `401` en `POST /users/login` en 15 min | Fuerza bruta o credenciales filtradas contra una o varias cuentas | Confirmar que T-07 (5 fallos por correo cada 15 min) sigue respondiendo `429`; revisar `failed_login_attempts`; si el volumen sigue, bloquear el login en el proxy hasta identificar el origen |
| `RATE-429` | advertencia | 50 o más `429` en cualquier ruta en 15 min | Los límites de T-06/T-07 están frenando tráfico; puede ser un ataque o un cliente con un bucle | Identificar la ruta en `/metrics`, revisar si el patrón es un cliente legítimo y ajustar la cuota solo con evidencia de uso real |
| `PROBE-404` | advertencia | 50 o más `404` en rutas inexistentes (`unmatched`) en 15 min | Sondeo de rutas: alguien está enumerando endpoints | Buscar las rutas pedidas en los logs de Traefik (los logs de la app no guardan la URL cruda); si es un escaneo, bloquear el origen en el proxy |
| `SERVER-5XX` | crítica | 1 o más respuestas `5xx` en 15 min | Error no controlado: falla la base, un proveedor o el propio código | Abrir el log del contenedor en la marca de tiempo, revisar la traza, comprobar base y proveedor LLM y, si el error llegó con un despliegue, revertirlo |
| `LATENCY-AGENT` | advertencia | p95 mayor que 7 000 ms en `POST /ai/message` | El asistente incumple el objetivo S3 | Revisar la latencia del proveedor LLM y si entró el respaldo Groq (ADR-0011); descartar saturación de la base |
| `LATENCY-CRUD` | advertencia | p95 mayor que 500 ms en cualquier ruta distinta del agente | Alguna operación CRUD incumple RNF-08 | Revisar el pool de conexiones, consultas lentas y CPU del contenedor; comparar la ruta con su p95 histórico |

Los umbrales viven en la tupla `REGLAS` del mismo archivo. Si se cambian, hay que actualizar
[`test_alertas.py`](../backend/tests/test_alertas.py), que prueba cada regla en el umbral y por
debajo.

## Cómo se confirma que se resolvió

1. La regla desaparece de `alerts` en `GET /metrics`.
2. Aparece un `alert_cleared` en los logs con la misma regla y ruta.
3. El contador correspondiente volvió por debajo del umbral.

## Límites conocidos

- La métrica es **en memoria del proceso**: se reinicia con cada despliegue y cada worker tiene
  la suya. No sustituye un sistema de métricas persistente.
- **No hay notificación externa** (correo, Slack, PagerDuty). Alguien tiene que mirar los logs o
  `/metrics`; por eso el riesgo residual de T-14 es medio y no bajo.
- La app no registra la IP de origen (RNF-05). Para atribuir un escaneo o una fuerza bruta hay
  que cruzar la hora con los logs del proxy.
- La ventana de 15 minutos es deliberadamente corta: una rafaga lenta y sostenida puede quedar
  por debajo del umbral. Los umbrales son iniciales y se ajustan con tráfico real.
- Las alertas de latencia dependen de que la ruta tenga muestras; una ruta nueva no alerta hasta
  recibir la primera petición.

## Relación con los requisitos

| Requisito | Cómo lo cubre la alerta |
|---|---|
| RNF-05 (logs sin datos sensibles) | Los eventos de alerta llevan regla, ruta, valor y umbral; no llevan cuerpos ni identificadores de usuario |
| RNF-08 (CRUD con p95 < 500 ms) | `LATENCY-CRUD` |
| S3 (asistente en 7 s o menos) | `LATENCY-AGENT` |
| RNF-03 (5 fallos por correo cada 15 min) | `AUTH-401` vigila el agregado del login |
| T-06 (límites de uso del LLM) | `RATE-429` |
| T-14 (ataques sin registro ni alerta) | Las seis reglas y este runbook |
