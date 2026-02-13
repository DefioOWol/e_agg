"""Тесты репозитория метаданных синхронизации."""

import asyncio

import pytest
from sqlalchemy.exc import IntegrityError

from app.orm.db_manager import db_manager
from app.orm.models import SyncStatus
from app.orm.repositories.sync_meta import (
    ISyncMetaRepository,
    SyncMetaRepository,
)


def _get_sync_meta_repository(session) -> ISyncMetaRepository:
    return SyncMetaRepository(session)


@pytest.mark.asyncio
async def test_get_or_add_new(session):
    """Проверить создание новых метаданных."""
    repo = _get_sync_meta_repository(session)
    sync_meta, is_new = await repo.get_or_add()
    assert is_new is True
    assert sync_meta.id == 1
    assert sync_meta.sync_status == SyncStatus.NEVER
    assert sync_meta.last_sync_time is None
    assert sync_meta.last_changed_at is None


@pytest.mark.asyncio
async def test_get_or_add_existing(session):
    """Проверить получение уже существующих метаданных."""
    repo = _get_sync_meta_repository(session)
    await repo.get_or_add()
    await session.flush()

    sync_meta, is_new = await repo.get_or_add()
    assert is_new is False
    assert sync_meta.id == 1
    assert sync_meta.sync_status == SyncStatus.NEVER


@pytest.mark.asyncio
async def test_get_or_add_concurrent():
    """Проверить конкурентные запросы на получение метаданных."""

    async def get_or_add_in_new_session():
        async with db_manager.session() as session:
            repo = _get_sync_meta_repository(session)
            _, is_new = await repo.get_or_add()
            try:
                await session.commit()
            except IntegrityError:
                return False
            return is_new

    results = await asyncio.gather(
        *[get_or_add_in_new_session() for _ in range(5)]
    )
    assert sum(results) == 1
