"""Composición de adaptadores de persistencia e identidad de Usuario."""

from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.adapters.outbound.sqlalchemy_telegram_link_repository import SqlAlchemyTelegramLinkRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.shared.adapters.outbound.database import get_session_factory


repository = SqlAlchemyUserRepository(get_session_factory())
password_hasher = Pbkdf2PasswordHasher()
token_service = JwtTokenService()
telegram_link_repository = SqlAlchemyTelegramLinkRepository(get_session_factory())
