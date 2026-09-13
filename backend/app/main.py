from fastapi import FastAPI

from backend.app.modules.usuario.adapters.outbound.provider import repository as usuario_repository, token_service as usuario_token_service
from backend.app.modules.usuario.application.ports.inbound.identity import configure_identity_service
from backend.app.modules.usuario.application.services.identity import IdentityServiceImpl

from backend.app.modules.academic.adapters.inbound.api import router as academic_router
from backend.app.modules.ai.adapters.inbound.api import router as ai_router
from backend.app.modules.reminders.adapters.inbound.http_controller import router as reminders_router
from backend.app.modules.usuario.adapters.inbound.api import router as usuario_router

identity_service = IdentityServiceImpl(usuario_repository, usuario_token_service)
configure_identity_service(identity_service)

app = FastAPI(title="TAIA")

app.include_router(academic_router)
app.include_router(usuario_router)
app.include_router(ai_router)
app.include_router(reminders_router)


@app.get("/health")
def health():
    return {"status": "ok"}