"""Outbound adapters for the Reminders bounded context."""

from .repository_provider import get_reminder_repository

__all__ = ["get_reminder_repository"]
