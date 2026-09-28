"""Logs estructurados y métrica de latencia de la API HTTP.

Cada petición produce una línea JSON en stdout (la recoge `docker logs`) y
alimenta la métrica que expone `GET /metrics`. La métrica se guarda en memoria
del proceso: se reinicia con cada despliegue.

Los logs solo llevan método, ruta, estado, duración e identificador de usuario;
nunca cuerpos, tokens ni mensajes del usuario (RNF-05).
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import deque
from math import ceil

from fastapi import FastAPI, Request

from app.shared.clock import now_bogota

logger = logging.getLogger("taia")

# Umbrales de latencia p95 ligados a los escenarios de calidad.
AGENT_ROUTE = "POST /ai/message"
AGENT_TARGET_MS = 7000  # S3: respuesta del asistente en 7 s o menos.
CRUD_TARGET_MS = 500  # RNF-08: operaciones CRUD con p95 < 500 ms.
SAMPLES_PER_ROUTE = 1000


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
    """Duraciones recientes por ruta para calcular el p95."""

    def __init__(self) -> None:
        self._durations: dict[str, deque[float]] = {}
        self._requests: dict[str, int] = {}
        self._server_errors: dict[str, int] = {}

    def record(self, route: str, status: int, duration_ms: float) -> None:
        self._durations.setdefault(route, deque(maxlen=SAMPLES_PER_ROUTE)).append(duration_ms)
        self._requests[route] = self._requests.get(route, 0) + 1
        if status >= 500:
            self._server_errors[route] = self._server_errors.get(route, 0) + 1

    def reset(self) -> None:
        self._durations.clear()
        self._requests.clear()
        self._server_errors.clear()

    def snapshot(self) -> dict:
        routes = {}
        for route, durations in sorted(self._durations.items()):
            is_agent = route == AGENT_ROUTE
            target_ms = AGENT_TARGET_MS if is_agent else CRUD_TARGET_MS
            p95_ms = _percentile(durations, 95)
            routes[route] = {
                "requests": self._requests[route],
                "server_errors": self._server_errors.get(route, 0),
                "p95_ms": round(p95_ms, 1),
                "target_p95_ms": target_ms,
                "quality_reference": "S3" if is_agent else "RNF-08",
                "within_target": p95_ms <= target_ms,
            }
        return {
            "metric": "http_request_duration_p95_ms",
            "window": f"últimas {SAMPLES_PER_ROUTE} peticiones por ruta desde el último arranque",
            "routes": routes,
        }


def _percentile(values: deque[float], percent: int) -> float:
    ordered = sorted(values)
    return ordered[max(ceil(len(ordered) * percent / 100) - 1, 0)]


metrics = LatencyMetrics()


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

    @app.get("/metrics", include_in_schema=False)
    def read_metrics() -> dict:
        return metrics.snapshot()
