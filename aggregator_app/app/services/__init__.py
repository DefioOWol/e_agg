"""Список импортируемых сервисов."""

from app.services.events import EventsService
from app.services.events_provider import EventsProviderClient
from app.services.sync import scheduler, sync_service
from app.services.tickets import TicketsService

__all__ = [
    "EventsService",
    "EventsProviderClient",
    "scheduler",
    "sync_service",
    "TicketsService",
]
