"""Тесты сервиса уведомлений."""

from unittest.mock import MagicMock

import pytest

from app.orm.models.outbox import Outbox
from app.services.notification import (
    CapashinoNotificationClient,
    INotificationClient,
)
from tests.helpers import get_datetime_now, get_external_client_mock_response


def _get_notification_client() -> INotificationClient:
    return CapashinoNotificationClient()


def _get_outbox() -> Outbox:
    return Outbox(
        id=1,
        payload={"ticket_id": "123", "event_id": "123", "seat": "A1"},
        created_at=get_datetime_now(),
    )


def test_get_body_from_outbox():
    client = _get_notification_client()
    body = client.get_body_from_outbox(_get_outbox())
    assert "message" in body
    assert "reference_id" in body
    assert "idempotency_key" in body


@pytest.mark.asyncio
async def test_notify():
    client = _get_notification_client()
    mock_session = MagicMock()
    mock_session.post.return_value = get_external_client_mock_response(
        {"success": True}
    )
    client._session = mock_session

    outbox = _get_outbox()
    result = await client.notify(outbox)

    mock_session.post.assert_called_once_with(
        "/api/notifications", json=client.get_body_from_outbox(outbox)
    )
    assert result == {"success": True}
