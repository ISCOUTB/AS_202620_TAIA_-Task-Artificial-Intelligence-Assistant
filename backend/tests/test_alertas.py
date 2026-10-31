"""Alertas de T-14: umbrales, transiciones y exportación por `/metrics`."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.adapters.inbound import observability
from app.shared.adapters.inbound.auth import get_authenticated_user_id
from app.shared.adapters.inbound.observability import (
    AlertMonitor,
    AlertRule,
    LatencyMetrics,
    evaluar_reglas,
)


def _datos(status_counts: dict[str, int] | None = None, server_errors: int = 0, p95_ms: float = 10) -> dict:
    return {
        "status_counts": status_counts or {},
        "server_errors": server_errors,
        "p95_ms": p95_ms,
    }


def _snapshot(**routes: dict) -> dict:
    return {"routes": routes}


def test_la_metrica_cuenta_estados_y_errores_de_servidor():
    metrics = LatencyMetrics()
    metrics.record("GET /x", 200, 10, now=1000)
    metrics.record("GET /x", 404, 12, now=1001)
    metrics.record("GET /x", 404, 13, now=1002)
    metrics.record("GET /x", 500, 20, now=1003)

    datos = metrics.snapshot(now=1004)["routes"]["GET /x"]

    assert datos["status_counts"] == {"200": 1, "404": 2, "500": 1}
    assert datos["server_errors"] == 1
    assert datos["requests"] == 4


def test_los_contadores_de_estado_vencen_con_la_ventana():
    metrics = LatencyMetrics()
    metrics.record("GET /x", 404, 10, now=1000)
    metrics.record("GET /x", 500, 10, now=1000)

    dentro = metrics.snapshot(now=1000 + observability.ALERT_WINDOW_S - 1)["routes"]["GET /x"]
    fuera = metrics.snapshot(now=1000 + observability.ALERT_WINDOW_S + 1)["routes"]["GET /x"]

    assert dentro["status_counts"] == {"404": 1, "500": 1}
    assert dentro["server_errors"] == 1
    assert fuera["status_counts"] == {}
    assert fuera["server_errors"] == 0


def test_el_tope_de_eventos_no_infla_los_contadores():
    metrics = LatencyMetrics()
    for _ in range(observability.MAX_EVENTS_PER_ROUTE + 5):
        metrics.record("GET /x", 404, 1, now=1000)

    datos = metrics.snapshot(now=1000)["routes"]["GET /x"]

    assert datos["status_counts"] == {"404": observability.MAX_EVENTS_PER_ROUTE}


def test_cada_regla_de_estado_dispara_en_su_umbral():
    casos = [
        ("AUTH-401", "POST /users/login", {"401": 20}),
        ("RATE-429", "GET /x", {"429": 50}),
        ("PROBE-404", "unmatched", {"404": 50}),
    ]

    for identificador, ruta, conteo in casos:
        alertas = evaluar_reglas(_snapshot(**{ruta: _datos(conteo)}))

        assert [alerta["rule"] for alerta in alertas] == [identificador]
        assert alertas[0]["value"] == conteo[next(iter(conteo))]


def test_una_regla_no_dispara_debajo_del_umbral():
    casos = [
        ("POST /users/login", {"401": 19}),
        ("GET /x", {"429": 49}),
        ("unmatched", {"404": 49}),
    ]

    for ruta, conteo in casos:
        assert evaluar_reglas(_snapshot(**{ruta: _datos(conteo)})) == []


def test_una_sola_respuesta_5xx_dispara_la_alerta_critica():
    alertas = evaluar_reglas(_snapshot(**{"GET /x": _datos(server_errors=1)}))

    assert [alerta["rule"] for alerta in alertas] == ["SERVER-5XX"]
    assert alertas[0]["severity"] == "critical"


def test_la_alerta_de_latencia_del_agente_usa_el_objetivo_s3():
    alertas = evaluar_reglas(_snapshot(**{"POST /ai/message": _datos(p95_ms=7001)}))

    assert [alerta["rule"] for alerta in alertas] == ["LATENCY-AGENT"]
    assert evaluar_reglas(_snapshot(**{"POST /ai/message": _datos(p95_ms=7000)})) == []


def test_la_alerta_de_latencia_crud_excluye_al_agente():
    assert [alerta["rule"] for alerta in evaluar_reglas(_snapshot(**{"GET /x": _datos(p95_ms=501)}))] == [
        "LATENCY-CRUD"
    ]
    assert evaluar_reglas(_snapshot(**{"GET /x": _datos(p95_ms=500)})) == []
    # El agente tiene su propio umbral (S3): no debe disparar además el de CRUD.
    assert [alerta["rule"] for alerta in evaluar_reglas(_snapshot(**{"POST /ai/message": _datos(p95_ms=9000)}))] == [
        "LATENCY-AGENT"
    ]


def test_una_ventana_sana_no_produce_alertas():
    sano = _snapshot(
        **{
            "POST /users/login": _datos({"200": 30, "401": 5}),
            "GET /academic/tasks": _datos({"200": 100}, p95_ms=120),
            "unmatched": _datos({"404": 3}),
            "POST /ai/message": _datos({"200": 10}, p95_ms=2500),
        }
    )

    assert evaluar_reglas(sano) == []


def _monitor_de_prueba() -> AlertMonitor:
    regla = AlertRule(
        id="TEST-401",
        severity="critical",
        metric="status",
        threshold=2,
        message="rafaga de prueba",
        status=401,
        route="POST /x",
    )
    return AlertMonitor((regla,))


def test_el_monitor_registra_solo_las_transiciones(caplog):
    caplog.set_level(logging.INFO, logger="taia")
    monitor = _monitor_de_prueba()
    fallo = _snapshot(**{"POST /x": _datos({"401": 2})})
    exito = _snapshot(**{"POST /x": _datos({})})

    assert len(monitor.observar(fallo)) == 1
    assert monitor.observar(fallo) == []
    assert monitor.snapshot()[0]["rule"] == "TEST-401"

    monitor.observar(exito)

    eventos = [registro.getMessage() for registro in caplog.records if registro.name == "taia"]
    assert eventos.count("alert_triggered") == 1
    assert eventos.count("alert_cleared") == 1
    assert monitor.snapshot() == []


def test_metrics_expone_las_alertas_activas():
    observability.metrics.reset()
    observability.alertas.reset()
    app = FastAPI()
    observability.install_observability(app)
    app.dependency_overrides[get_authenticated_user_id] = lambda: "prueba"
    client = TestClient(app)

    try:
        umbral = next(regla.threshold for regla in observability.REGLAS if regla.id == "PROBE-404")
        for _ in range(int(umbral)):
            assert client.get("/ruta-inexistente").status_code == 404

        cuerpo = client.get("/metrics").json()

        assert "probe" in "".join(alerta["rule"] for alerta in cuerpo["alerts"]).lower()
        assert cuerpo["routes"]["unmatched"]["status_counts"]["404"] >= umbral
        assert cuerpo["alerts"][0]["route"] == "unmatched"
    finally:
        app.dependency_overrides.clear()
        observability.metrics.reset()
        observability.alertas.reset()
