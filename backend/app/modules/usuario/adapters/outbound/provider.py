"""Composición de adaptadores de persistencia e identidad de Usuario."""

from app.modules.usuario.adapters.outbound.in_memory_telegram_link_repository import InMemoryTelegramLinkRepository
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.shared.adapters.outbound.database import get_session_factory, use_in_memory_storage


def _build_user_repository() -> UserRepository:
    if use_in_memory_storage():
        return InMemoryUserRepository()
    return SqlAlchemyUserRepository(get_session_factory())


repository = _build_user_repository()
password_hasher = Pbkdf2PasswordHasher()
token_service = JwtTokenService()
telegram_link_repository = InMemoryTelegramLinkRepository()
