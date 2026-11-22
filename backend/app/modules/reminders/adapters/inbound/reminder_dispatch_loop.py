"""Proceso periódico que envía los recordatorios vencidos (RF-NOT-02, ADR-0012).

Es un adaptador de entrada: como una petición HTTP, dispara un caso de uso. Corre
dentro de la API, en el `lifespan`, y ejecuta el envío en un hilo para no bloquear
las peticiones. La idempotencia la garantiza el caso de uso, no este bucle.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from datetime import datetime

from app.shared.clock import Clock, now_bogota

logger = logging.getLogger("taia.reminders")

INTERVAL_SECONDS = 60.0


class ReminderDispatchLoop:
    """Ejecuta `dispatch(now)` cada `interval_seconds` mientras la API está viva.

    `enabled = False` lo desactiva de forma explícita: `start()` no lanza nada. Las
    pruebas lo usan así y llaman al caso de uso con un reloj inyectado.
    """

    def __init__(
        self,
        dispatch: Callable[[datetime], object],
        clock: Clock = now_bogota,
        interval_seconds: float = INTERVAL_SECONDS,
        enabled: bool = True,
    ) -> None:
        self._dispatch = dispatch
        self._clock = clock
        self._interval = interval_seconds
        self.enabled = enabled
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        if self.enabled and not self.running:
            self._task = asyncio.create_task(self._run(), name="reminder-dispatch")

    async def stop(self) -> None:
        """Cancela el bucle al apagar la API."""

        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def run_once(self) -> None:
        """Una ejecución. Un fallo se registra (sin datos del usuario, RNF-05) y no se propaga."""

        try:
            await asyncio.to_thread(self._dispatch, self._clock())
        except Exception as error:
            logger.error("reminder_dispatch_failed", extra={"fields": {"error": type(error).__name__}})

    async def _run(self) -> None:
        while True:
            await self.run_once()
            await asyncio.sleep(self._interval)
