from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from app.modules.usuario.adapters.outbound.provider import repository as usuario_repository, token_service as usuario_token_service
from app.modules.usuario.application.ports.inbound.identity import configure_identity_service
from app.modules.usuario.application.services.identity import IdentityServiceImpl

from app.modules.academic.adapters.outbound.repository_provider import get_subject_repository, get_task_repository
from app.modules.academic.application.ports.inbound.task_lookup import configure_academic_task_lookup
from app.modules.academic.application.ports.inbound.task_management import configure_academic_task_management
from app.modules.academic.application.services.task_lookup import AcademicTaskLookupService
from app.modules.academic.application.services.task_management import AcademicTaskManagementService

identity_service = IdentityServiceImpl(usuario_repository, usuario_token_service)
configure_identity_service(identity_service)

academic_repository = get_task_repository()
configure_academic_task_lookup(AcademicTaskLookupService(academic_repository))
configure_academic_task_management(AcademicTaskManagementService(academic_repository, get_subject_repository()))

# IA se compone aqui y no en su adaptador HTTP. Construir el LLM aqui mantiene
# un unico cliente httpx para toda la vida del proceso: antes se creaba uno por
# peticion y nunca se cerraba. Ademas, si falta GEMINI_API_KEY el proceso no
# arranca, en vez de responder 503 en cada peticion mientras /health dice ok.
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.adapters.outbound.gemini_llm import GeminiLLM
from app.modules.ai.adapters.outbound.sqlalchemy_conversation_store import (
    SqlAlchemyConversationStore,
)
from app.modules.ai.adapters.inbound.api import (
    configure_ai_use_case,
    router as ai_router,
)
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.shared.adapters.outbound.database import get_session_factory

gemini_llm = GeminiLLM.from_env()
configure_ai_use_case(
    HandleUserMessageUseCase(
        llm=gemini_llm,
        academic=AcademicGatewayAdapter(),
        conversations=SqlAlchemyConversationStore(get_session_factory()),
    )
)

from app.modules.academic.adapters.inbound.api import router as academic_router
from app.modules.academic.adapters.inbound.structure_api import (
    period_router as academic_period_router,
    schedule_router as academic_schedule_router,
    subjects_router as academic_subjects_router,
)
from app.modules.reminders.adapters.inbound.http_controller import router as reminders_router
from app.modules.usuario.adapters.inbound.api import router as usuario_router
from app.shared.adapters.inbound.observability import install_observability
from app.shared.adapters.inbound.readiness import require_database

from app.modules.academic.adapters.inbound.structure_api import configure_structure_use_cases
from app.modules.academic.adapters.outbound.repository_provider import (
    get_academic_period_repository, get_schedule_block_repository,
)
from app.modules.academic.application.use_cases.manage_subjects import ManageSubjectsUseCase
from app.modules.academic.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.modules.academic.application.use_cases.manage_academic_period import ManageAcademicPeriodUseCase
from app.modules.reminders.adapters.inbound.http_controller import (
    ReminderUseCases, configure_reminder_use_cases,
)
from app.modules.reminders.adapters.outbound.academic_task_lookup_adapter import AcademicTaskLookupAdapter
from app.modules.reminders.adapters.outbound.repository_provider import get_reminder_repository
from app.modules.reminders.adapters.outbound.notification_provider import get_notification_sender
from app.modules.academic.application.ports.inbound.task_lookup import get_academic_task_lookup
from app.modules.reminders.application.use_cases.create_reminder import CreateReminderUseCase
from app.modules.reminders.application.use_cases.list_reminders import ListRemindersUseCase
from app.modules.reminders.application.use_cases.get_reminder import GetReminderUseCase
from app.modules.reminders.application.use_cases.edit_reminder import EditReminderUseCase
from app.modules.reminders.application.use_cases.delete_reminder import DeleteReminderUseCase
from app.modules.reminders.application.use_cases.mark_reminder_completed import MarkReminderCompletedUseCase
from app.modules.reminders.application.use_cases.schedule_notification import ScheduleNotificationUseCase
from app.modules.reminders.application.use_cases.send_notification import SendNotificationUseCase

configure_structure_use_cases(
    ManageSubjectsUseCase(get_subject_repository(), get_schedule_block_repository(), academic_repository),
    ManageScheduleUseCase(get_subject_repository(), get_schedule_block_repository()),
    ManageAcademicPeriodUseCase(get_academic_period_repository()),
)
reminder_repository = get_reminder_repository()
configure_reminder_use_cases(ReminderUseCases(
    create=CreateReminderUseCase(reminder_repository, AcademicTaskLookupAdapter(get_academic_task_lookup().get_summary)),
    list=ListRemindersUseCase(reminder_repository),
    get=GetReminderUseCase(reminder_repository),
    edit=EditReminderUseCase(reminder_repository),
    delete=DeleteReminderUseCase(reminder_repository),
    complete=MarkReminderCompletedUseCase(reminder_repository),
    schedule_notification=ScheduleNotificationUseCase(reminder_repository),
    send_notification=SendNotificationUseCase(get_notification_sender(), reminder_repository),
))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Libera el cliente httpx del proveedor de lenguaje al apagar.

    El cliente se crea una sola vez en el composition root y se comparte, asi
    que el pool de conexiones se reutiliza y hay que cerrarlo explicitamente.
    """

    yield
    gemini_llm.close()


app = FastAPI(
    title="TAIA",
    version="1.0.0",
    description="Contrato versionado de la API HTTP principal de TAIA. La API utiliza HTTP síncrono y JSON para solicitudes y respuestas.",
    lifespan=lifespan,
)

install_observability(app)

app.include_router(academic_router)
app.include_router(academic_subjects_router)
app.include_router(academic_schedule_router)
app.include_router(academic_period_router)
app.include_router(usuario_router)
app.include_router(ai_router)
app.include_router(reminders_router)


@app.get("/health")
def health(database_ready: None = Depends(require_database)):
    return {"status": "ok"}


@app.get("/mockup")
def mockup():
    """Provide a lightweight endpoint for validating deployments."""
    return {"message": "CD pipeline test successful"}
