"""Конфигурация тестов API."""

from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_events_service, get_tickets_service
from app.main import app
from app.services.events import EventsService
from app.services.events_provider import EventsPaginator, EventsProviderParser
from app.services.sync import SyncService, get_sync_service
from app.services.tickets import TicketsService
from tests.helpers import FakeEventsProviderClient, FakeUnitOfWork


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def provider_client():
    return FakeEventsProviderClient()


@pytest.fixture
def events_service(uow, provider_client):
    return EventsService(uow, provider_client)


@pytest.fixture
def tickets_service(uow, provider_client):
    return TicketsService(uow, provider_client)


@pytest.fixture
def sync_service(uow, provider_client):
    scheduler = MagicMock()
    scheduler.modify_job = MagicMock()
    return SyncService(
        uow,
        scheduler,
        provider_client,
        EventsPaginator(),
        EventsProviderParser(),
    )


@pytest_asyncio.fixture
async def client(events_service, tickets_service, sync_service):
    app.dependency_overrides[get_events_service] = lambda: events_service
    app.dependency_overrides[get_tickets_service] = lambda: tickets_service
    app.dependency_overrides[get_sync_service] = lambda: sync_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
