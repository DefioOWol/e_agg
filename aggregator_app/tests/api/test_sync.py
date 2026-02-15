"""Тесты API синхронизации."""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.services.sync import SyncService


@pytest.mark.asyncio
async def test_trigger_sync(client: AsyncClient, sync_service: SyncService):
    response = await client.post("/sync/trigger")
    assert response.status_code == status.HTTP_202_ACCEPTED
    sync_service._scheduler.modify_job.assert_called_once()
