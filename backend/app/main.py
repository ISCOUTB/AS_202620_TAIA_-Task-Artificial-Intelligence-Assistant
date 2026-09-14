from fastapi import FastAPI

from backend.app.modules.usuario.adapters.outbound.provider import repository as usuario_repository, token_service as usuario_token_service
from backend.app.modules.usuario.application.ports.inbound.identity import configure_identity_service
from backend.app.modules.usuario.application.services.identity import IdentityServiceImpl

from backend.app.modules.academic.adapters.outbound.repository_provider import get_task_repository
from backend.app.modules.academic.application.ports.inbound.task_lookup import configure_academic_task_lookup
from backend.app.modules.academic.application.ports.inbound.task_management import configure_academic_task_management
from backend.app.modules.academic.application.services.task_lookup import AcademicTaskLookupService
from backend.app.modules.academic.application.services.task_management import AcademicTaskManagementService

identity_service = IdentityServiceImpl(usuario_repository, usuario_token_service)
configure_identity_service(identity_service)

academic_repository = get_task_repository()
configure_academic_task_lookup(AcademicTaskLookupService(academic_repository))
configure_academic_task_management(AcademicTaskManagementService(academic_repository))

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