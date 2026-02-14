"""Конфигурация тестов сервисов."""

import pytest

from app.services.events import EventsService
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
