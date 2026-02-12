from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.orm.models import EventStatus
from app.services.events_provider import (
    EventsPaginator,
    EventsProviderClient,
    EventsProviderParser,
)
from tests.services.helpers import (
    FakeEventsProviderClient,
    get_raw_event,
    get_raw_member,
)


def _get_mock_response(expected_result: dict) -> AsyncMock:
    mock_response = AsyncMock()
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    mock_response.json = AsyncMock(return_value=expected_result)
    return mock_response


@pytest.mark.asyncio
async def test_get_events():
    expected_result = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }
    mock_response = _get_mock_response(expected_result)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    client = EventsProviderClient()
    client._session = mock_session

    changed_at = date(2000, 1, 1)
    result = await client.get_events(changed_at)

    mock_session.get.assert_called_once_with(
        f"/api/events/?changed_at={changed_at.isoformat()}"
    )
    assert result == expected_result

    cursor = "abc123"
    await client.get_events(changed_at, cursor)
    mock_session.get.assert_called_with(
        f"/api/events/?changed_at={changed_at.isoformat()}&cursor={cursor}"
    )


@pytest.mark.asyncio
async def test_get_seats():
    expected_result = {"seats": ["A1", "A2", "A3"]}
    mock_response = _get_mock_response(expected_result)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    client = EventsProviderClient()
    client._session = mock_session

    event_id = uuid4()
    result = await client.get_seats(event_id)

    mock_session.get.assert_called_once_with(f"/api/events/{event_id}/seats/")
    assert result == expected_result


@pytest.mark.asyncio
async def test_register_member():
    expected_result = {"ticket_id": str(uuid4())}
    mock_response = _get_mock_response(expected_result)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_response

    client = EventsProviderClient()
    client._session = mock_session

    event_id = uuid4()
    member_data = get_raw_member()
    result = await client.register_member(event_id, member_data)

    mock_session.post.assert_called_once_with(
        f"/api/events/{event_id}/register/", json=member_data
    )
    assert result == expected_result


@pytest.mark.asyncio
async def test_unregister_member():
    expected_result = {"success": True}
    mock_response = _get_mock_response(expected_result)

    mock_session = MagicMock()
    mock_session.delete.return_value = mock_response

    client = EventsProviderClient()
    client._session = mock_session

    event_id = uuid4()
    ticket_id = str(uuid4())
    result = await client.unregister_member(event_id, ticket_id)

    mock_session.delete.assert_called_once_with(
        f"/api/events/{event_id}/unregister/", json={"ticket_id": ticket_id}
    )
    assert result == expected_result


def test_extract_cursor():
    cursor = EventsProviderClient.extract_cursor(
        {
            "next": (
                "http://example.com/api/events/"
                "?changed_at=2024-01-01&cursor=cursor-token"
            )
        }
    )
    assert cursor == "cursor-token"
    cursor = EventsProviderClient.extract_cursor({})
    assert cursor is None


@pytest.mark.asyncio
async def test_events_paginator_empty():
    client = FakeEventsProviderClient(
        pages={
            None: {
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            }
        }
    )
    paginator = EventsPaginator()(client, date(2000, 1, 1))
    events = [event async for event in paginator]
    assert events == []


@pytest.mark.asyncio
async def test_events_paginator_non_empty():
    client = FakeEventsProviderClient(
        pages={
            None: {
                "next": "abc123",
                "results": ["event1", "event2"],
            },
            "abc123": {
                "next": None,
                "results": ["event3"],
            },
        }
    )
    paginator = EventsPaginator()(client, date(2000, 1, 1))
    events = [event async for event in paginator]
    assert events == ["event1", "event2", "event3"]


def test_events_provider_parser():
    parser = EventsProviderParser()
    event_dict, place_dict = parser.parse_event_dict(get_raw_event())

    assert "place" not in event_dict
    assert "place_id" in event_dict
    assert event_dict["place_id"] == place_dict["id"]
    assert "number_of_visitors" not in event_dict
    assert isinstance(event_dict["status"], EventStatus)

    for keys, data_dict in (
        (
            (
                "event_time",
                "registration_deadline",
                "changed_at",
                "created_at",
                "status_changed_at",
            ),
            event_dict,
        ),
        (
            ("changed_at", "created_at"),
            place_dict,
        ),
    ):
        for key in keys:
            assert isinstance(data_dict[key], datetime)
            assert data_dict[key].tzinfo is UTC
