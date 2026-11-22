from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends

from app.modules.usuario.adapters.outbound.provider import (
    repository as usuario_repository,
    session_repository as usuario_session_repository,
    token_service as usuario_token_service,
)
from app.modules.usuario.application.ports.inbound.identity import configure_identity_service
from app.modules.usuario.application.services.identity import IdentityServiceImpl

from app.modules.academic.adapters.outbound.repository_provider import get_subject_repository, get_task_repository
from app.modules.academic.application.ports.inbound.task_lookup import configure_academic_task_lookup
from app.modules.academic.application.ports.inbound.task_management import configure_academic_task_management
from app.modules.academic.application.services.task_lookup import AcademicTaskLookupService
from app.modules.academic.application.services.task_management import AcademicTaskManagementService

identity_service = IdentityServiceImpl(usuario_repository, usuario_token_service, usuario_session_repository)
configure_identity_service(identity_service)

# Frente A: dispositivos y estado de la cuenta para Reminders (RF-NOT-01, RF-USR-09).
from app.modules.usuario.application.ports.inbound.user_devices import configure_user_device_directory
from app.modules.usuario.application.services.user_devices import UserDeviceDirectoryService

configure_user_device_directory(UserDeviceDirectoryService(usuario_repository, usuario_session_repository))

academic_repository = get_task_repository()
configure_academic_task_lookup(AcademicTaskLookupService(academic_repository))
academic_task_management = AcademicTaskManagementService(academic_repository, get_subject_repository())
configure_academic_task_management(academic_task_management)

# IA se compone aqui y no en su adaptador HTTP. Construir el LLM aqui mantiene
# un unico cliente httpx para toda la vida del proceso: antes se creaba uno por
# peticion y nunca se cerraba. Ademas, si falta GEMINI_API_KEY el proceso no
# arranca, en vez de responder 503 en cada peticion mientras /health dice ok.
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.adapters.outbound.fallback_llm import FallbackLLM
from app.modules.ai.adapters.outbound.sqlalchemy_conversation_store import (
    SqlAlchemyConversationStore,
)
from app.modules.ai.adapters.inbound.api import (
    configure_ai_use_case,
    router as ai_router,
)
from app.modules.ai.application.ports.inbound.agent_chat import configure_agent_chat
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.application.use_cases.telegram_chat import TelegramAgentChat
from app.shared.adapters.outbound.database import get_session_factory

# Frente D · ADR-0013: Groq es el principal, con cada credencial configurada en
# orden, y Gemini el respaldo. Sin credenciales de Groq, el agente usa solo Gemini.
llm = FallbackLLM.from_env()
ai_use_case = HandleUserMessageUseCase(
    llm=llm,
    academic=AcademicGatewayAdapter(),
    conversations=SqlAlchemyConversationStore(get_session_factory()),
)
configure_ai_use_case(ai_use_case)
# Frente D · RF-TEL-04: Telegram usa el mismo caso de uso, con el canal telegram.
configure_agent_chat(TelegramAgentChat(ai_use_case))

from app.modules.academic.adapters.inbound.api import router as academic_router
from app.modules.academic.adapters.inbound.structure_api import (
    period_router as academic_period_router,
    schedule_router as academic_schedule_router,
    subjects_router as academic_subjects_router,
)
from app.modules.reminders.adapters.inbound.http_controller import router as reminders_router
from app.modules.usuario.adapters.inbound.api import router as usuario_router
from app.modules.usuario.adapters.inbound.telegram_webhook import router as telegram_webhook_router
from app.shared.adapters.inbound.observability import install_observability
from app.shared.adapters.inbound.readiness import require_database

from app.modules.academic.adapters.inbound.structure_api import configure_structure_use_cases
from app.modules.academic.adapters.outbound.repository_provider import (
    get_academic_period_repository, get_schedule_block_repository,
)
from app.modules.academic.application.use_cases.manage_subjects import ManageSubjectsUseCase
from app.modules.academic.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.modules.academic.application.use_cases.manage_academic_period import ManageAcademicPeriodUseCase
# Frente B: Reminders (RF-REC-01…06, RF-NOT-02…04, ADR-0012)
from app.modules.academic.application.ports.inbound.task_management import get_academic_task_management
from app.modules.reminders.adapters.inbound.http_controller import (
    ReminderUseCases, configure_reminder_use_cases,
)
from app.modules.reminders.adapters.inbound.notifications_controller import (
    configure_notification_inbox,
    router as notifications_router,
)
from app.modules.reminders.adapters.inbound.reminder_dispatch_loop import ReminderDispatchLoop
from app.modules.reminders.adapters.outbound.academic_task_lookup_adapter import AcademicTaskLookupAdapter
from app.modules.reminders.adapters.outbound.fcm_push_sender import FcmPushSender
from app.modules.reminders.adapters.outbound.repository_provider import (
    get_notification_repository, get_reminder_repository,
)
from app.modules.reminders.application.ports.inbound.task_reminder_sync import (
    configure_task_reminder_reader, configure_task_reminder_sync,
)
from app.modules.reminders.application.services.task_reminder_sync import TaskReminderSyncService
from app.modules.reminders.application.use_cases.create_reminder import CreateReminderUseCase
from app.modules.reminders.application.use_cases.delete_reminder import DeleteReminderUseCase
from app.modules.reminders.application.use_cases.dispatch_due_reminders import DispatchDueRemindersUseCase
from app.modules.reminders.application.use_cases.edit_reminder import EditReminderUseCase
from app.modules.reminders.application.use_cases.get_reminder import GetReminderUseCase
from app.modules.reminders.application.use_cases.list_reminders import ListRemindersUseCase
from app.modules.reminders.application.use_cases.notification_inbox import NotificationInboxUseCase
from app.modules.usuario.application.ports.inbound.user_devices import get_user_device_directory

configure_structure_use_cases(
    ManageSubjectsUseCase(get_subject_repository(), get_schedule_block_repository(), academic_repository),
    ManageScheduleUseCase(get_subject_repository(), get_schedule_block_repository()),
    ManageAcademicPeriodUseCase(get_academic_period_repository()),
)

# Frente C: la API de tareas usa la misma instancia que publica AcademicTaskManagement
# (RF-TAR-02, RF-TAR-05), el calendario proyecta el horario (RF-TAR-11) y AcademicInsights
# lo reutiliza para el agente (RF-AGT-10, 12 y 13). Estadísticas del perfil (RF-PRF-01).
from app.modules.academic.adapters.inbound.api import configure_task_api
from app.modules.academic.adapters.inbound.calendar_api import (
    configure_calendar_use_case,
    router as academic_calendar_router,
)
from app.modules.academic.adapters.inbound.statistics_api import (
    configure_statistics_use_case,
    router as academic_statistics_router,
)
from app.modules.academic.application.ports.inbound.academic_insights import configure_academic_insights
from app.modules.academic.application.services.academic_insights import AcademicInsightsService
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.modules.academic.application.use_cases.profile_statistics import ProfileStatisticsUseCase

academic_calendar = AcademicCalendarUseCase(
    academic_repository, get_subject_repository(), get_schedule_block_repository(), get_academic_period_repository()
)
configure_task_api(academic_task_management)
configure_calendar_use_case(academic_calendar)

# Plan de estudio (RF-EST-01…03): Academic valida y guarda; AI solo sugiere con el LLM.
from app.modules.academic.adapters.inbound.study_plan_api import (
    configure_study_plan_use_case,
    router as academic_study_plan_router,
)
from app.modules.academic.adapters.outbound.ai_study_session_advisor import AiStudySessionAdvisor
from app.modules.academic.adapters.outbound.repository_provider import get_study_plan_repository
from app.modules.academic.application.use_cases.manage_study_plan import ManageStudyPlanUseCase
from app.modules.ai.application.ports.inbound.study_plan_advisor import configure_study_plan_advisor
from app.modules.ai.application.use_cases.advise_study_plan import AdviseStudyPlanUseCase

configure_study_plan_advisor(AdviseStudyPlanUseCase(llm))
configure_study_plan_use_case(ManageStudyPlanUseCase(
    get_study_plan_repository(), academic_repository, get_subject_repository(), academic_calendar,
    AiStudySessionAdvisor(),
))
configure_academic_insights(AcademicInsightsService(academic_repository, get_subject_repository(), academic_calendar))
configure_statistics_use_case(
    ProfileStatisticsUseCase(academic_repository, get_subject_repository(), get_academic_period_repository())
)

# Frente B: composición de Reminders.
reminder_repository = get_reminder_repository()
notification_repository = get_notification_repository()
reminder_tasks = AcademicTaskLookupAdapter(get_academic_task_management())
configure_reminder_use_cases(ReminderUseCases(
    create=CreateReminderUseCase(reminder_repository, reminder_tasks),
    list=ListRemindersUseCase(reminder_repository),
    get=GetReminderUseCase(reminder_repository),
    edit=EditReminderUseCase(reminder_repository, reminder_tasks),
    delete=DeleteReminderUseCase(reminder_repository),
))
task_reminder_sync = TaskReminderSyncService(reminder_repository, reminder_tasks)
configure_task_reminder_sync(task_reminder_sync)
configure_task_reminder_reader(task_reminder_sync)
configure_notification_inbox(NotificationInboxUseCase(notification_repository))
# Sin FIREBASE_CREDENTIALS_JSON, push_sender es None: las notificaciones quedan en la bandeja (RNF-09).
push_sender = FcmPushSender.from_env()


def dispatch_due_reminders(now):
    """RF-NOT-02. El directorio de dispositivos se resuelve en cada ejecución: lo configura Usuario."""

    return DispatchDueRemindersUseCase(
        reminder_repository, notification_repository, reminder_tasks, get_user_device_directory(), push_sender,
    ).execute(now)


# ADR-0012: el bucle corre en el lifespan. `reminder_dispatch_loop.enabled = False` lo desactiva.
reminder_dispatch_loop = ReminderDispatchLoop(dispatch_due_reminders)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Libera el cliente httpx del proveedor de lenguaje al apagar.

    El cliente se crea una sola vez en el composition root y se comparte, asi
    que el pool de conexiones se reutiliza y hay que cerrarlo explicitamente.
    """

    # Frente B: envío periódico de recordatorios (RF-NOT-02, ADR-0012).
    reminder_dispatch_loop.start()
    try:
        yield
    finally:
        await reminder_dispatch_loop.stop()
        llm.close()


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
app.include_router(academic_calendar_router)  # Frente C
app.include_router(academic_statistics_router)  # Frente C
app.include_router(academic_study_plan_router)
app.include_router(usuario_router)
app.include_router(telegram_webhook_router)
app.include_router(ai_router)
app.include_router(reminders_router)
# Frente B: bandeja de notificaciones (RF-NOT-03).
app.include_router(notifications_router)


@app.get("/health")
def health(database_ready: Annotated[None, Depends(require_database)]):
    return {"status": "ok"}


@app.get("/mockup")
def mockup():
    """Provide a lightweight endpoint for validating deployments."""
    return {"message": "CD pipeline test successful"}
