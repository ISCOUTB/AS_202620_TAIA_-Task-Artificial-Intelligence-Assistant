"""RF-NOT-02 y ADR-0012 · Bucle de envío dentro de la API, sin dormir ni usar la base de datos."""

import asyncio
import logging
from datetime import datetime

from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.modules.reminders.adapters.inbound.reminder_dispatch_loop import INTERVAL_SECONDS, ReminderDispatchLoop
from app.shared.clock import BOGOTA_TZ

NOW = datetime(2026, 10, 7, 18, 0, tzinfo=BOGOTA_TZ)


def test_runs_at_least_every_minute_rf_not_02_adr_0012():
    assert INTERVAL_SECONDS <= 60


def test_run_once_dispatches_with_the_injected_clock_rf_not_02():
    calls: list[datetime] = []
    loop = ReminderDispatchLoop(calls.append, clock=lambda: NOW)

    asyncio.run(loop.run_once())

    assert calls == [NOW]


def test_run_once_logs_the_error_and_does_not_raise_adr_0012(caplog):
    def failing(_now):
        raise RuntimeError("fallo")

    loop = ReminderDispatchLoop(failing, clock=lambda: NOW)

    with caplog.at_level(logging.ERROR, logger="taia.reminders"):
        asyncio.run(loop.run_once())

    assert [record.message for record in caplog.records] == ["reminder_dispatch_failed"]


def test_loop_keeps_running_after_a_failure_adr_0012():
    async def scenario() -> list[datetime]:
        calls: list[datetime] = []
        done = asyncio.Event()

        def dispatch(now):
            calls.append(now)
            if len(calls) == 1:
                raise RuntimeError("fallo")
            done.set()

        loop = ReminderDispatchLoop(dispatch, clock=lambda: NOW, interval_seconds=0)
        loop.start()
        await asyncio.wait_for(done.wait(), timeout=5)
        await loop.stop()
        return calls

    assert len(asyncio.run(scenario())) >= 2


def test_stop_cancels_the_loop_adr_0012():
    async def scenario() -> tuple[bool, bool]:
        loop = ReminderDispatchLoop(lambda _now: None, clock=lambda: NOW, interval_seconds=3600)
        loop.start()
        started = loop.running
        await loop.stop()
        return started, loop.running

    assert asyncio.run(scenario()) == (True, False)


def test_disabled_loop_does_not_start_adr_0012():
    async def scenario() -> bool:
        loop = ReminderDispatchLoop(lambda _now: None, enabled=False)
        loop.start()
        return loop.running

    assert asyncio.run(scenario()) is False


def test_lifespan_skips_the_disabled_loop_rf_not_02_adr_0012(monkeypatch):
    monkeypatch.setattr(main.reminder_dispatch_loop, "enabled", False)
    # El lifespan cierra los clientes HTTP del LLM al salir; las demás pruebas los siguen usando.
    monkeypatch.setattr(main.llm, "close", lambda: None)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert main.reminder_dispatch_loop.running is False
