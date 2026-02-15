"""Тесты API событий."""

from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from app.orm.models import EventStatus
from tests.helpers import (
    FakeEventsProviderClient,
    FakeUnitOfWork,
    create_event,
)


@pytest.mark.asyncio
async def test_get_events(client: AsyncClient, uow: FakeUnitOfWork):
    event1 = create_event()
    event2 = create_event()
    uow.events.events = {event1.id: event1, event2.id: event2}

    response = await client.get("/events")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2
    assert len(data["results"]) == 2

    ids = {result["id"] for result in data["results"]}
    assert str(event1.id) in ids
    assert str(event2.id) in ids


@pytest.mark.asyncio
async def test_get_events_with_pagination(
    client: AsyncClient, uow: FakeUnitOfWork
):
    event1 = create_event()
    event2 = create_event()
    uow.events.events = {event1.id: event1, event2.id: event2}

    response = await client.get("/events", params={"page": 1, "page_size": 1})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == str(event1.id)
    assert data["next"] is not None
    assert data["previous"] is None

    response = await client.get(data["next"])

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == str(event2.id)
    assert data["next"] is None
    assert data["previous"] is not None


@pytest.mark.asyncio
async def test_get_events_with_filter(client: AsyncClient, uow: FakeUnitOfWork):
    event = create_event()
    uow.events.events = {event.id: event}

    response = await client.get("/events", params={"date_from": "2000-01-01"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1

    response = await client.get("/events", params={"date_from": "3000-01-01"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


@pytest.mark.asyncio
async def test_get_event_by_id(client: AsyncClient, uow: FakeUnitOfWork):
    event = create_event()
    uow.events.events = {event.id: event}

    response = await client.get(f"/events/{event.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(event.id)
    assert data["place"]["seats_pattern"] == event.place.seats_pattern


@pytest.mark.asyncio
async def test_get_event_by_id_not_found(client: AsyncClient):
    response = await client.get(f"/events/{uuid4()}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


@pytest.mark.asyncio
async def test_get_event_seats(
    client: AsyncClient,
    uow: FakeUnitOfWork,
    provider_client: FakeEventsProviderClient,
):
    event = create_event(status=EventStatus.PUBLISHED)
    uow.events.events = {event.id: event}
    provider_client.kwargs["seats"] = {"seats": ["A1", "A2", "A3"]}

    response = await client.get(f"/events/{event.id}/seats")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["event_id"] == str(event.id)
    assert data["available_seats"] == ["A1", "A2", "A3"]


@pytest.mark.asyncio
async def test_get_event_seats_event_not_found(client: AsyncClient):
    response = await client.get(f"/events/{uuid4()}/seats")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


@pytest.mark.asyncio
async def test_get_event_seats_event_not_published(
    client: AsyncClient, uow: FakeUnitOfWork
):
    event = create_event(status=EventStatus.NEW)
    uow.events.events = {event.id: event}
    response = await client.get(f"/events/{event.id}/seats")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Event is not published"
