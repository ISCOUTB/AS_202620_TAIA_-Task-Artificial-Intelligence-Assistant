"""Composición de adaptadores de persistencia e identidad de Usuario."""

from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.adapters.outbound.resend_password_reset_mailer import ResendPasswordResetMailer
from app.modules.usuario.adapters.outbound.sqlalchemy_failed_login_attempt_repository import (
    SqlAlchemyFailedLoginAttemptRepository,
)
from app.modules.usuario.adapters.outbound.sqlalchemy_password_reset_code_repository import (
    SqlAlchemyPasswordResetCodeRepository,
)
from app.modules.usuario.adapters.outbound.sqlalchemy_password_reset_request_repository import (
    SqlAlchemyPasswordResetRequestRepository,
)
from app.modules.usuario.adapters.outbound.sqlalchemy_session_repository import SqlAlchemySessionRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_telegram_link_repository import SqlAlchemyTelegramLinkRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.shared.adapters.outbound.database import get_session_factory


repository = SqlAlchemyUserRepository(get_session_factory())
password_hasher = Pbkdf2PasswordHasher()
token_service = JwtTokenService()
telegram_link_repository = SqlAlchemyTelegramLinkRepository(get_session_factory())
failed_login_attempt_repository = SqlAlchemyFailedLoginAttemptRepository(get_session_factory())
session_repository = SqlAlchemySessionRepository(get_session_factory())
password_reset_request_repository = SqlAlchemyPasswordResetRequestRepository(get_session_factory())
password_reset_code_repository = SqlAlchemyPasswordResetCodeRepository(get_session_factory())
# None si falta RESEND_API o RESEND_FROM: la solicitud de recuperación responde 503 (RF-USR-08).
password_reset_mailer = ResendPasswordResetMailer.from_env()
