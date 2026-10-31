"""Logs estructurados, métrica de latencia y alertas de la API HTTP.

Cada petición produce una línea JSON en stdout (la recoge `docker logs`) y
alimenta la métrica que expone `GET /metrics`. La métrica se guarda en memoria
del proceso: se reinicia con cada despliegue.

Los logs solo llevan método, ruta, estado, duración e identificador de usuario;
nunca cuerpos, tokens ni mensajes del usuario (RNF-05).

Las alertas de T-14 se evalúan sobre esa misma ventana: cuando una regla pasa de
inactiva a activa se emite `alert_triggered`, y al volver a la normalidad,
`alert_cleared`. Así un ataque deja rastro aunque nadie esté mirando `/metrics`.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import deque
from dataclasses import dataclass
from math import ceil
from threading import Lock

from fastapi import Depends, FastAPI, Request

from app.shared.adapters.inbound.auth import get_authenticated_user_id
from app.shared.clock import now_bogota

logger = logging.getLogger("taia")

# Umbrales de latencia p95 ligados a los escenarios de calidad.
AGENT_ROUTE = "POST /ai/message"
AGENT_TARGET_MS = 7000  # S3: respuesta del asistente en 7 s o menos.
CRUD_TARGET_MS = 500  # RNF-08: operaciones CRUD con p95 < 500 ms.
SAMPLES_PER_ROUTE = 1000
LOGIN_ROUTE = "POST /users/login"

# Las alertas de rafaga cuentan peticiones de los ultimos 15 minutos, igual que
# la ventana de intentos fallidos de RNF-03. Sin vencimiento, una alerta de 404
# quedaria activa para siempre y nunca se emitiria `alert_cleared`.
ALERT_WINDOW_S = 15 * 60
MAX_EVENTS_PER_ROUTE = 2000


@dataclass(frozen=True)
class AlertRule:
    """Regla de alerta evaluada sobre la ventana de la métrica.

    `metric` vale "status" (cuenta de un código concreto), "server_errors"
    (respuestas 5xx) o "p95" (latencia). `route` limita la regla a una ruta;
    sin ruta se aplica a todas.
    """

    id: str
    severity: str
    metric: str
    threshold: float
    message: str
    status: int | None = None
    route: str | None = None
    excludes_agent: bool = False


REGLAS = (
    AlertRule(
        id="AUTH-401",
        severity="critical",
        metric="status",
        threshold=20,
        message="Rafaga de 401 en el login: posible fuerza bruta o credenciales filtradas",
        status=401,
        route=LOGIN_ROUTE,
    ),
    AlertRule(
        id="RATE-429",
        severity="warning",
        metric="status",
        threshold=50,
        message="Rafaga de 429: el limite de uso esta frenando trafico",
        status=429,
    ),
    AlertRule(
        id="PROBE-404",
        severity="warning",
        metric="status",
        threshold=50,
        message="Sondeo de rutas: muchos 404 en la ventana",
        status=404,
    ),
    AlertRule(
        id="SERVER-5XX",
        severity="critical",
        metric="server_errors",
        threshold=1,
        message="Errores 5xx en la ventana: revisar los logs del contenedor",
    ),
    AlertRule(
        id="LATENCY-AGENT",
        severity="warning",
        metric="p95",
        threshold=AGENT_TARGET_MS,
        message="El agente supera el objetivo de 7 s (S3)",
        route=AGENT_ROUTE,
    ),
    AlertRule(
        id="LATENCY-CRUD",
        severity="warning",
        metric="p95",
        threshold=CRUD_TARGET_MS,
        message="Una ruta CRUD supera el p95 de 500 ms (RNF-08)",
        excludes_agent=True,
    ),
)



class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": now_bogota().isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class LatencyMetrics:
    """Duraciones recientes por ruta y contadores de estado por ventana."""

    def __init__(self) -> None:
        self._durations: dict[str, deque[float]] = {}
        self._requests: dict[str, int] = {}
        self._server_errors: dict[str, int] = {}
        self._status_counts: dict[str, dict[int, int]] = {}
        self._events: dict[str, deque[tuple[float, int]]] = {}

    def _prune(self, route: str, now: float, enforce_capacity: bool = False) -> None:
        """Descarta los eventos que ya salieron de la ventana de alertas."""

        events = self._events.setdefault(route, deque())
        limite = now - ALERT_WINDOW_S
        # El tope por cantidad evita que una rafaga sostenida crezca sin limite;
        # hay que descontarlo a mano porque un deque con maxlen descartaria en
        # silencio y dejaria los contadores inflados. Solo se aplica al registrar,
        # no al leer, para no perder un evento recien contado.
        while events and (
            events[0][0] < limite
            or (enforce_capacity and len(events) >= MAX_EVENTS_PER_ROUTE)
        ):
            _, status = events.popleft()
            if status >= 500:
                self._server_errors[route] -= 1
            contadores = self._status_counts[route]
            contadores[status] -= 1
            if not contadores[status]:
                del contadores[status]

    def record(self, route: str, status: int, duration_ms: float, now: float | None = None) -> None:
        momento = time.monotonic() if now is None else now
        self._prune(route, momento, enforce_capacity=True)
        self._durations.setdefault(route, deque(maxlen=SAMPLES_PER_ROUTE)).append(duration_ms)
        self._requests[route] = self._requests.get(route, 0) + 1
        if status >= 500:
            self._server_errors[route] = self._server_errors.get(route, 0) + 1
        contadores = self._status_counts.setdefault(route, {})
        contadores[status] = contadores.get(status, 0) + 1
        self._events[route].append((momento, status))

    def reset(self) -> None:
        self._durations.clear()
        self._requests.clear()
        self._server_errors.clear()
        self._status_counts.clear()
        self._events.clear()

    def snapshot(self, now: float | None = None) -> dict:
        momento = time.monotonic() if now is None else now
        routes = {}
        for route, durations in sorted(self._durations.items()):
            self._prune(route, momento)
            is_agent = route == AGENT_ROUTE
            target_ms = AGENT_TARGET_MS if is_agent else CRUD_TARGET_MS
            p95_ms = _percentile(durations, 95)
            routes[route] = {
                "requests": self._requests[route],
                "server_errors": self._server_errors.get(route, 0),
                "status_counts": {
                    str(status): total
                    for status, total in sorted(self._status_counts.get(route, {}).items())
                },
                "p95_ms": round(p95_ms, 1),
                "target_p95_ms": target_ms,
                "quality_reference": "S3" if is_agent else "RNF-08",
                "within_target": p95_ms <= target_ms,
            }
        return {
            "metric": "http_request_duration_p95_ms",
            "window": (
                f"p95 de las ultimas {SAMPLES_PER_ROUTE} peticiones por ruta; "
                f"los contadores de estado cubren {ALERT_WINDOW_S // 60} minutos"
            ),
            "routes": routes,
        }


def _percentile(values: deque[float], percent: int) -> float:
    ordered = sorted(values)
    return ordered[max(ceil(len(ordered) * percent / 100) - 1, 0)]


def evaluar_reglas(snapshot: dict, reglas: tuple[AlertRule, ...] = REGLAS) -> list[dict]:
    """Devuelve las alertas activas para la ventana actual."""

    alertas: list[dict] = []
    for route, datos in snapshot.get("routes", {}).items():
        for regla in reglas:
            if regla.route is not None and regla.route != route:
                continue
            if regla.metric == "p95":
                if regla.excludes_agent and route == AGENT_ROUTE:
                    continue
                valor = datos["p95_ms"]
                supera = valor > regla.threshold
            elif regla.metric == "status":
                valor = datos.get("status_counts", {}).get(str(regla.status), 0)
                supera = valor >= regla.threshold
            elif regla.metric == "server_errors":
                valor = datos.get("server_errors", 0)
                supera = valor >= regla.threshold
            else:  # pragma: no cover - las reglas se declaran en este archivo
                continue

            if supera:
                alertas.append(
                    {
                        "rule": regla.id,
                        "severity": regla.severity,
                        "route": route,
                        "value": valor,
                        "threshold": regla.threshold,
                        "message": regla.message,
                    }
                )
    return alertas


class AlertMonitor:
    """Guarda el estado de las alertas y registra solo los cambios."""

    def __init__(self, reglas: tuple[AlertRule, ...] = REGLAS) -> None:
        self._reglas = reglas
        self._activas: dict[tuple[str, str], dict] = {}
        self._lock = Lock()

    def reset(self) -> None:
        with self._lock:
            self._activas.clear()

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [alerta for _, alerta in sorted(self._activas.items())]

    def observar(self, snapshot: dict) -> list[dict]:
        actuales = {
            (alerta["rule"], alerta["route"]): alerta
            for alerta in evaluar_reglas(snapshot, self._reglas)
        }
        with self._lock:
            nuevas = [alerta for clave, alerta in actuales.items() if clave not in self._activas]
            resueltas = [alerta for clave, alerta in self._activas.items() if clave not in actuales]
            self._activas = actuales

        for alerta in nuevas:
            logger.warning("alert_triggered", extra={"fields": alerta})
        for alerta in resueltas:
            logger.info(
                "alert_cleared",
                extra={"fields": {"rule": alerta["rule"], "route": alerta["route"]}},
            )
        return nuevas


metrics = LatencyMetrics()
alertas = AlertMonitor()


def install_observability(app: FastAPI) -> None:
    configure_logging()

    @app.middleware("http")
    async def log_and_measure(request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            # Plantilla de la ruta (/academic/tasks/{task_id}), no la URL cruda.
            matched = request.scope.get("route")
            route = f"{request.method} {matched.path}" if matched else "unmatched"
            metrics.record(route, status, duration_ms)
            alertas.observar(metrics.snapshot())
            logger.info(
                "http_request",
                extra={
                    "fields": {
                        "method": request.method,
                        "route": matched.path if matched else None,
                        "status": status,
                        "duration_ms": round(duration_ms, 1),
                        "user_id": getattr(request.state, "user_id", None),
                    }
                },
            )

    # RT-01: /metrics no está entre las excepciones de la autenticación JWT.
    # Revela las rutas y su tráfico, así que no se publica sin sesión.
    @app.get("/metrics", include_in_schema=False, dependencies=[Depends(get_authenticated_user_id)])
    def read_metrics() -> dict:
        return {**metrics.snapshot(), "alerts": alertas.snapshot()}
