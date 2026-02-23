"""Тесты сервиса inbox."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.inbox import InboxService
from tests.helpers import FakeUnitOfWork


@pytest.mark.asyncio
async def test_init_job(inbox_service: InboxService, scheduler: MagicMock):
    await inbox_service.init_jobs()
    assert scheduler.add_job.called


@pytest.mark.asyncio
async def test_process_expired(
    inbox_service: InboxService, uow: FakeUnitOfWork
):
    uow.inbox.delete_expired = AsyncMock()
    await inbox_service.process_expired()
    assert uow.inbox.delete_expired.called
    assert uow.committed


@pytest.mark.asyncio
async def test_get_inbox(inbox_service: InboxService, uow: FakeUnitOfWork):
    uow.inbox.get = AsyncMock()
    await inbox_service.get_inbox("key")
    assert uow.inbox.get.called
    assert uow.inbox.get.call_args[0][0] == "key"
