"""Конфигурация тестов сервисов."""

from unittest.mock import MagicMock

import pytest

from app.services.events import EventsService
from app.services.events_provider import EventsPaginator, EventsProviderParser
from app.services.sync import SyncService
from app.services.tickets import TicketsService
from tests.services.helpers import FakeEventsProviderClient, FakeUnitOfWork


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def client():
    return FakeEventsProviderClient()


@pytest.fixture
def events_service(uow, client):
    return EventsService(uow, client)


@pytest.fixture
def tickets_service(uow, client):
    return TicketsService(uow, client)


@pytest.fixture
def scheduler():
    scheduler = MagicMock()
    scheduler.add_job = MagicMock()
    scheduler.modify_job = MagicMock()
    return scheduler


@pytest.fixture
def sync_service(uow, scheduler, client):
    return SyncService(
        uow, scheduler, client, EventsPaginator(), EventsProviderParser()
    )
