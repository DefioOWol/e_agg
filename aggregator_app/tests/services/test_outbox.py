"""Тесты сервиса outbox."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orm.models import OutboxStatus, OutboxType
from app.services.outbox import OutboxService
from tests.helpers import FakeUnitOfWork


def test_init_job(outbox_service: OutboxService, scheduler: MagicMock):
    outbox_service.init_job()
    assert scheduler.add_job.called


@pytest.mark.asyncio
async def test_process_waiting_empty(
    outbox_service: OutboxService, uow: FakeUnitOfWork
):
    await outbox_service.process_waiting()
    assert len(uow.outbox.outbox) == 0
    assert not uow.committed


@pytest.mark.asyncio
async def test_process_waiting_update_status(
    outbox_service: OutboxService, uow: FakeUnitOfWork
):
    item = uow.outbox.create(OutboxType.TICKET_REGISTER, {"ticket_id": "123"})
    outbox_service._process_ticket_register = AsyncMock(return_value=None)
    await outbox_service.process_waiting()
    assert uow.outbox.outbox[item.id].status == OutboxStatus.SENT
    assert uow.committed


@pytest.mark.asyncio
async def test_process_waiting_handle_error(
    outbox_service: OutboxService, uow: FakeUnitOfWork
):
    item = uow.outbox.create(OutboxType.TICKET_REGISTER, {"ticket_id": "123"})
    outbox_service._process_ticket_register = AsyncMock(
        side_effect=TimeoutError
    )
    await outbox_service.process_waiting()
    assert uow.outbox.outbox[item.id].status == OutboxStatus.WAITING
    assert not uow.committed
