"""Тесты репозитория идемпотентности."""

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.repositories.inbox import IInboxRepository, InboxRepository
from tests.helpers import get_datetime_now


def _get_inbox_repository(session: AsyncSession) -> IInboxRepository:
    return InboxRepository(session)


@pytest.mark.asyncio
async def test_create(session: AsyncSession):
    repo = _get_inbox_repository(session)
    inbox = repo.create("key", "hash", {"response": "response"})
    await session.flush()

    assert inbox.key == "key"
    assert inbox.request_hash == "hash"
    assert inbox.response == {"response": "response"}
    assert inbox.expires_at >= get_datetime_now()


@pytest.mark.asyncio
async def test_get(session: AsyncSession):
    repo = _get_inbox_repository(session)
    inbox = repo.create("key", "hash", {"response": "response"})
    await session.flush()

    inbox_got = await repo.get("key")
    assert inbox.key == inbox_got.key
    assert inbox.request_hash == inbox_got.request_hash
    assert inbox.response == inbox_got.response
    assert inbox.expires_at == inbox_got.expires_at


@pytest.mark.asyncio
async def test_get_none(session: AsyncSession):
    repo = _get_inbox_repository(session)
    inbox_got = await repo.get("key")
    assert inbox_got is None


@pytest.mark.asyncio
async def test_delete_expired(session: AsyncSession):
    repo = _get_inbox_repository(session)
    inbox = repo.create("key1", "hash", {"response": "response"})
    inbox.expires_at = get_datetime_now() - timedelta(hour=1)

    inbox = repo.create("key2", "hash", {"response": "response"})
    inbox.expires_at = get_datetime_now() + timedelta(hour=1)
    await session.flush()

    deleted = await repo.delete_expired()
    await session.flush()

    assert deleted == 1
    inbox_got = await repo.get("key1")
    assert inbox_got is None
    inbox_got = await repo.get("key2")
    assert inbox_got is not None


@pytest.mark.asyncio
async def test_delete_expired_none(session: AsyncSession):
    repo = _get_inbox_repository(session)
    deleted = await repo.delete_expired()
    assert deleted == 0
