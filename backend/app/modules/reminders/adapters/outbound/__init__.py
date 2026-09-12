"""Outbound adapters for the Reminders bounded context."""

from .in_memory_reminder_repository import InMemoryReminderRepository
from .repository_provider import get_reminder_repository

__all__ = ["InMemoryReminderRepository", "get_reminder_repository"]
