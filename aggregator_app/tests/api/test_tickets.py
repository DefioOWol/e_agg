"""Тесты API регистрации участников."""

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from app.orm.models import EventStatus, Inbox, Member
from app.services.utils import hash_dict
from tests.helpers import (
    FakeEventsProviderClient,
    FakeUnitOfWork,
    create_event,
    get_raw_member,
)


@pytest.mark.asyncio
async def test_register(
    client: AsyncClient,
    uow: FakeUnitOfWork,
    provider_client: FakeEventsProviderClient,
):
    event = create_event(
        status=EventStatus.PUBLISHED, timedelta=timedelta(hours=1)
    )
    uow.events.events = {event.id: event}

    provider_client.kwargs["seats"] = {"seats": ["A1", "A2"]}
    ticket_id = str(uuid4())
    provider_client.kwargs["ticket_id"] = {"ticket_id": ticket_id}

    member_data = get_raw_member() | {"event_id": str(event.id)}
    response = await client.post("/tickets", json=member_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["ticket_id"] == ticket_id


@pytest.mark.asyncio
async def test_register_event_not_found(client: AsyncClient):
    member_data = get_raw_member() | {"event_id": str(uuid4())}
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


@pytest.mark.parametrize("event_status", [EventStatus.NEW, EventStatus.OTHER])
@pytest.mark.asyncio
async def test_register_event_not_published(
    event_status: EventStatus, client: AsyncClient, uow: FakeUnitOfWork
):
    event = create_event(status=event_status, timedelta=timedelta(hours=1))
    uow.events.events = {event.id: event}
    member_data = get_raw_member() | {"event_id": str(event.id)}
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Event is not published"


@pytest.mark.asyncio
async def test_register_seat_not_available(
    client: AsyncClient,
    uow: FakeUnitOfWork,
    provider_client: FakeEventsProviderClient,
):
    event = create_event(
        status=EventStatus.PUBLISHED, timedelta=timedelta(hours=1)
    )
    uow.events.events = {event.id: event}
    provider_client.kwargs["seats"] = {"seats": ["A1"]}

    member_data = get_raw_member() | {"event_id": str(event.id), "seat": "A2"}
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Seat is not available"


@pytest.mark.asyncio
async def test_register_deadline_expired(
    client: AsyncClient, uow: FakeUnitOfWork
):
    event = create_event(status=EventStatus.PUBLISHED)
    event.registration_deadline -= timedelta(hours=1)
    uow.events.events = {event.id: event}

    member_data = get_raw_member() | {"event_id": str(event.id)}
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "The registration time has expired"


@pytest.mark.asyncio
async def test_register_validation_email_error(client: AsyncClient):
    member_data = get_raw_member() | {
        "event_id": str(uuid4()),
        "email": "invalid_email",
    }
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json()["body"]


@pytest.mark.asyncio
async def test_register_validation_seat_error(client: AsyncClient):
    member_data = get_raw_member() | {
        "event_id": str(uuid4()),
        "seat": "invalid_seat",
    }
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "seat" in response.json()["body"]


@pytest.mark.asyncio
async def test_register_idempotency_key_non_exists(
    client: AsyncClient,
    uow: FakeUnitOfWork,
    provider_client: FakeEventsProviderClient,
):
    event = create_event(
        status=EventStatus.PUBLISHED, timedelta=timedelta(hours=1)
    )
    uow.events.events = {event.id: event}

    provider_client.kwargs["seats"] = {"seats": ["A1"]}
    ticket_id = str(uuid4())
    provider_client.kwargs["ticket_id"] = {"ticket_id": ticket_id}

    member_data = get_raw_member() | {"event_id": str(event.id)}
    hashed_request = hash_dict(member_data)
    member_data["idempotency_key"] = "123"
    response = await client.post("/tickets", json=member_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert uow.inbox.inbox["123"].request_hash == hashed_request
    assert uow.inbox.inbox["123"].response == {"ticket_id": ticket_id}


@pytest.mark.asyncio
async def test_register_idempotency_key_already_exists(
    client: AsyncClient, uow: FakeUnitOfWork
):
    member_data = get_raw_member() | {"event_id": str(uuid4())}
    saved_response = {"ticket_id": "123"}
    inbox = Inbox(
        key="123", request_hash=hash_dict(member_data), response=saved_response
    )
    uow.inbox.inbox = {inbox.key: inbox}

    member_data["idempotency_key"] = inbox.key
    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == saved_response


@pytest.mark.asyncio
async def test_register_idempotency_key_conflict(
    client: AsyncClient, uow: FakeUnitOfWork
):
    member_data = get_raw_member() | {"event_id": "123"}
    inbox = Inbox(key="123", request_hash=hash_dict(member_data))
    uow.inbox.inbox = {inbox.key: inbox}

    member_data["idempotency_key"] = inbox.key
    member_data["event_id"] = str(uuid4())

    response = await client.post("/tickets", json=member_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Idempotency key already exists"


@pytest.mark.asyncio
async def test_unregister(
    client: AsyncClient,
    uow: FakeUnitOfWork,
):
    event = create_event(
        status=EventStatus.PUBLISHED, timedelta=timedelta(hours=1)
    )
    ticket_id = uuid4()
    member = Member(
        **get_raw_member(), event_id=event.id, event=event, ticket_id=ticket_id
    )
    uow.members.members = {ticket_id: member}

    response = await client.delete(f"/tickets/{ticket_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_unregister_member_not_found(client: AsyncClient):
    response = await client.delete(f"/tickets/{uuid4()}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Member not found"


@pytest.mark.asyncio
async def test_unregister_event_already_passed(
    client: AsyncClient, uow: FakeUnitOfWork
):
    event = create_event(status=EventStatus.PUBLISHED)
    event.event_time -= timedelta(hours=1)
    ticket_id = uuid4()
    member = Member(
        **get_raw_member(), event_id=event.id, event=event, ticket_id=ticket_id
    )
    uow.members.members = {ticket_id: member}

    response = await client.delete(f"/tickets/{ticket_id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "The event has already passed"
