"""Конфигурация тестов сервисов."""

import pytest

from app.services.events import EventsService
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
