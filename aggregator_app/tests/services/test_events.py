"""Тесты сервиса событий."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.api.filters import EventFilter
from app.orm.models import Event
from app.services.events import EventsService
from app.services.events_provider import EventsProviderParser
from tests.services.helpers import (
    FakeEventRepository,
    FakeEventsProviderClient,
    FakeUnitOfWork,
    get_raw_event,
)


@pytest.mark.asyncio
async def test_get_paginated_events_and_count(
    events_service: EventsService, uow: FakeUnitOfWork
):
    parser = EventsProviderParser()
    event1 = Event(**parser.parse_event_dict(get_raw_event())[0])
    event2 = Event(**parser.parse_event_dict(get_raw_event())[0])
    uow.events = FakeEventRepository({event1.id: event1, event2.id: event2})

    events, count = await events_service.get_paginated(EventFilter(), 1, None)
    assert len(events) == 2
    assert count == 2
    assert event1 in events
    assert event2 in events


@pytest.mark.asyncio
async def test_get_paginated_with_filter(
    events_service: EventsService, uow: FakeUnitOfWork
):
    parser = EventsProviderParser()
    event = Event(**parser.parse_event_dict(get_raw_event())[0])
    uow.events = FakeEventRepository({event.id: event})

    filter_ = EventFilter(date_from=date.fromisoformat("2000-01-01"))
    events, count = await events_service.get_paginated(filter_, 1, None)
    assert len(events) == 1
    assert count == 1

    filter_ = EventFilter(date_from=date.fromisoformat("3000-01-01"))
    events, count = await events_service.get_paginated(filter_, 1, None)
    assert len(events) == 0
    assert count == 0


@pytest.mark.asyncio
async def test_get_by_id(events_service: EventsService, uow: FakeUnitOfWork):
    parser = EventsProviderParser()
    event = Event(**parser.parse_event_dict(get_raw_event())[0])
    uow.events = FakeEventRepository({event.id: event})
    event_id = event.id

    result = await events_service.get_by_id(event_id)
    assert result is not None
    assert result.id == event_id


@pytest.mark.asyncio
async def test_get_by_id_not_found(events_service: EventsService):
    result = await events_service.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_seats(
    events_service: EventsService, client: FakeEventsProviderClient
):
    client.kwargs["seats"] = {"seats": ["A1", "A2", "A3"]}
    seats = await events_service.get_seats(uuid4())
    assert seats == ["A1", "A2", "A3"]


@pytest.mark.asyncio
async def test_get_seats_raises_error(uow: FakeUnitOfWork):
    client = MagicMock()
    client.get_seats = AsyncMock(side_effect=TimeoutError)
    events_service = EventsService(uow, client)

    with pytest.raises(HTTPException) as exc:
        await events_service.get_seats(uuid4())

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
