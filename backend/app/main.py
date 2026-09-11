from fastapi import FastAPI

from backend.app.modules.academic.adapters.inbound.api import router as academic_router
from backend.app.modules.ai.adapters.inbound.api import router as ai_router
from backend.app.modules.reminders.adapters.inbound.http_controller import router as reminders_router
from backend.app.modules.usuario.adapters.inbound.api import router as usuario_router

app = FastAPI(title="TAIA")

app.include_router(academic_router)
app.include_router(usuario_router)
app.include_router(ai_router)
app.include_router(reminders_router)


@app.get("/health")
def health():
    return {"status": "ok"}