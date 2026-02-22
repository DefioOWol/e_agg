"""Конфигурация тестов сервисов."""

from unittest.mock import MagicMock

import pytest

from app.services.events import EventsService
from app.services.events_provider import EventsPaginator, EventsProviderParser
from app.services.outbox import OutboxService
from app.services.sync import SyncService
from app.services.tickets import TicketsService
from tests.helpers import FakeEventsProviderClient, FakeUnitOfWork


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def events_provider_client():
    return FakeEventsProviderClient()


@pytest.fixture
def events_service(uow, events_provider_client):
    return EventsService(uow, events_provider_client)


@pytest.fixture
def tickets_service(uow, events_provider_client):
    return TicketsService(uow, events_provider_client)


@pytest.fixture
def scheduler():
    scheduler = MagicMock()
    scheduler.add_job = MagicMock()
    scheduler.modify_job = MagicMock()
    return scheduler


@pytest.fixture
def sync_service(uow, scheduler, events_provider_client):
    return SyncService(
        uow,
        scheduler,
        events_provider_client,
        EventsPaginator(),
        EventsProviderParser(),
    )


@pytest.fixture
def outbox_service(uow, scheduler):
    outbox_service = OutboxService(uow, scheduler)
    outbox_service._client = MagicMock()
    return outbox_service
