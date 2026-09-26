"""Composición de adaptadores de persistencia e identidad de Usuario."""

from app.modules.usuario.adapters.outbound.in_memory_telegram_link_repository import InMemoryTelegramLinkRepository
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher

repository = InMemoryUserRepository()
password_hasher = Pbkdf2PasswordHasher()
token_service = JwtTokenService()
telegram_link_repository = InMemoryTelegramLinkRepository()
