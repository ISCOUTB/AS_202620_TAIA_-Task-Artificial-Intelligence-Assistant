from fastapi import FastAPI

from app.modules.academic.adapters.inbound.api import router as academic_router
from app.modules.ai.adapters.inbound.api import router as ai_router
from app.modules.reminders.adapters.inbound.http_controller import router as reminders_router
from app.modules.usuario.adapters.inbound.api import router as usuario_router

app = FastAPI(
    title="TAIA",
    version="1.0.0",
    description="Contrato versionado de la API HTTP principal de TAIA. La API utiliza HTTP síncrono y JSON para solicitudes y respuestas.",
)

app.include_router(academic_router)
app.include_router(usuario_router)
app.include_router(ai_router)
app.include_router(reminders_router)


@app.get("/health")
def health():
    return {"status": "ok"}