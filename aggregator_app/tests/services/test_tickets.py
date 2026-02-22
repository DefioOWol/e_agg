"""Тесты сервиса регистрации участников."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiohttp import ClientResponseError
from fastapi import HTTPException, status

from app.orm.models import OutboxStatus, OutboxType
from app.services.tickets import TicketsService
from tests.helpers import (
    FakeEventsProviderClient,
    FakeUnitOfWork,
    get_datetime_now,
    get_raw_member,
)


@pytest.mark.asyncio
async def test_register_member(
    uow: FakeUnitOfWork, events_provider_client: FakeEventsProviderClient
):
    event_id = uuid4()
    member_data = get_raw_member()
    ticket_id = str(uuid4())

    events_provider_client.kwargs["ticket_id"] = {"ticket_id": ticket_id}
    service = TicketsService(uow, events_provider_client)

    result_ticket_id = await service.register(event_id, member_data)

    assert result_ticket_id == ticket_id
    assert ticket_id in uow.members.members

    member = uow.members.members[ticket_id]
    assert member.event_id == str(event_id)
    assert uow.committed


@pytest.mark.asyncio
async def test_register_member_with_outbox(
    uow: FakeUnitOfWork, events_provider_client: FakeEventsProviderClient
):
    event_id = uuid4()
    member_data = get_raw_member()
    ticket_id = str(uuid4())

    events_provider_client.kwargs["ticket_id"] = {"ticket_id": ticket_id}
    service = TicketsService(uow, events_provider_client)
    await service.register(event_id, member_data)

    assert len(uow.outbox.outbox) == 1
    assert uow.outbox.outbox[1].type == OutboxType.TICKET_REGISTER
    assert uow.outbox.outbox[1].payload == member_data | {
        "event_id": str(event_id),
        "ticket_id": ticket_id,
    }
    assert uow.outbox.outbox[1].status == OutboxStatus.WAITING
    assert uow.outbox.outbox[1].created_at <= get_datetime_now()
    assert uow.committed


@pytest.mark.asyncio
async def test_unregister_member(
    uow: FakeUnitOfWork, events_provider_client: FakeEventsProviderClient
):
    event_id = uuid4()
    ticket_id = uuid4()

    member_data = get_raw_member()
    member_data.update({"event_id": event_id, "ticket_id": ticket_id})
    uow.members.create(member_data)

    service = TicketsService(uow, events_provider_client)
    await service.unregister(event_id, ticket_id)

    assert ticket_id not in uow.members.members
    assert uow.committed


@pytest.mark.asyncio
async def test_get_by_id(tickets_service: TicketsService, uow: FakeUnitOfWork):
    ticket_id = uuid4()

    member_data = get_raw_member()
    member_data.update({"event_id": uuid4(), "ticket_id": ticket_id})
    uow.members.create(member_data)

    member = await tickets_service.get_by_id(ticket_id)

    assert member is not None
    assert member.ticket_id == ticket_id


@pytest.mark.asyncio
async def test_get_by_id_not_found(tickets_service: TicketsService):
    member = await tickets_service.get_by_id(uuid4())
    assert member is None


@pytest.mark.parametrize(
    ("method", "arg"), [("register", get_raw_member()), ("unregister", uuid4())]
)
@pytest.mark.asyncio
async def test_raises_400_on_client_400_error(
    method: str, arg: Any, uow: FakeUnitOfWork
):
    mock_response = AsyncMock(
        side_effect=ClientResponseError(
            request_info=None, history=None, status=status.HTTP_400_BAD_REQUEST
        )
    )
    client = MagicMock()
    setattr(client, method + "_member", mock_response)
    service = TicketsService(uow, client)

    with pytest.raises(HTTPException) as exc:
        await getattr(service, method)(uuid4(), arg)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert not uow.committed


@pytest.mark.parametrize(
    ("method", "arg"), [("register", get_raw_member()), ("unregister", uuid4())]
)
@pytest.mark.asyncio
async def test_raises_500_on_client_other_errors(
    method: str, arg, uow: FakeUnitOfWork
):
    mock_response = AsyncMock(side_effect=TimeoutError)
    client = MagicMock()
    setattr(client, method + "_member", mock_response)
    service = TicketsService(uow, client)

    with pytest.raises(HTTPException) as exc:
        await getattr(service, method)(uuid4(), arg)

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert not uow.committed
