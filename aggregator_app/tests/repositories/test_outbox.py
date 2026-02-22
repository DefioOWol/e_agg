"""Тесты репозитория очереди событий."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.models import Outbox, OutboxStatus, OutboxType
from app.orm.repositories.outbox import IOutboxRepository, OutboxRepository
from tests.helpers import get_datetime_now


def _get_outbox_repository(session: AsyncSession) -> IOutboxRepository:
    return OutboxRepository(session)


@pytest.mark.asyncio
async def test_create(session: AsyncSession):
    repo = _get_outbox_repository(session)
    result = repo.create(OutboxType.TICKET_REGISTER, {"ticket_id": "123"})
    await session.flush()

    assert result.id == 1
    assert result.type == OutboxType.TICKET_REGISTER
    assert result.payload == {"ticket_id": "123"}
    assert result.status == OutboxStatus.WAITING
    assert result.created_at <= get_datetime_now()


@pytest.mark.asyncio
async def test_get_waiting_empty(session: AsyncSession):
    repo = _get_outbox_repository(session)
    result = await repo.get_waiting()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_waiting(session: AsyncSession):
    repo = _get_outbox_repository(session)
    repo.create(OutboxType.TICKET_REGISTER, {"ticket_id": "123"})
    repo.create(OutboxType.TICKET_REGISTER, {"ticket_id": "456"})
    await session.flush()
    result = await repo.get_waiting()

    assert len(result) == 2
    assert result[0].payload == {"ticket_id": "123"}
    assert result[0].status == OutboxStatus.WAITING
    assert result[1].payload == {"ticket_id": "456"}
    assert result[1].status == OutboxStatus.WAITING


@pytest.mark.asyncio
async def test_update_status(session: AsyncSession):
    repo = _get_outbox_repository(session)
    result = repo.create(OutboxType.TICKET_REGISTER, {"ticket_id": "123"})
    await session.flush()
    updated = await repo.update_status(result.id, OutboxStatus.SENT)
    await session.flush()

    assert updated
    result_got = await session.get(Outbox, result.id)
    assert result_got.id == result.id
    assert result_got.type == result.type
    assert result_got.payload == result.payload
    assert result_got.status == OutboxStatus.SENT
    assert result_got.created_at == result.created_at
