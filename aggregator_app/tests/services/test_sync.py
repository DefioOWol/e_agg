"""Тесты сервиса синхронизации."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orm.models import SyncMeta, SyncStatus
from app.services.sync import SyncService
from tests.helpers import (
    FakeEventsProviderClient,
    FakeSyncMetaRepository,
    FakeUnitOfWork,
    get_datetime_now,
    get_raw_event,
)


@pytest.mark.asyncio
async def test_init_job(
    sync_service: SyncService, uow: FakeUnitOfWork, scheduler: MagicMock
):
    await sync_service.init_jobs()
    assert uow.sync_meta.meta is not None
    assert uow.sync_meta.meta.sync_status == SyncStatus.NEVER
    assert scheduler.add_job.called


@pytest.mark.asyncio
async def test_init_job_fix_pending_status(
    sync_service: SyncService, uow: FakeUnitOfWork
):
    meta = SyncMeta(id=1, sync_status=SyncStatus.PENDING)
    uow.sync_meta = FakeSyncMetaRepository(meta=meta)

    await sync_service.init_jobs()

    assert uow.sync_meta.meta.sync_status != SyncStatus.PENDING
    assert uow.committed


@pytest.mark.asyncio
async def test_trigger_job(sync_service: SyncService, scheduler: MagicMock):
    sync_service.trigger_job()
    assert scheduler.modify_job.called
    call_args = scheduler.modify_job.call_args
    assert call_args[0][0] == SyncService.SYNC_JOB_ID
    assert call_args[1]["next_run_time"] <= get_datetime_now()


@pytest.mark.asyncio
async def test_sync_skips_if_pending(
    sync_service: SyncService, uow: FakeUnitOfWork
):
    meta = SyncMeta(id=1, sync_status=SyncStatus.PENDING)
    uow.sync_meta = FakeSyncMetaRepository(meta=meta)
    await sync_service.sync()
    assert uow.sync_meta.meta.sync_status == SyncStatus.PENDING


@pytest.mark.asyncio
async def test_sync_update_db(
    sync_service: SyncService,
    events_provider_client: FakeEventsProviderClient,
    uow: FakeUnitOfWork,
):
    events = []
    events_ids = set()
    places_ids = set()
    latest_changed_at = date.fromisoformat("2000-01-01")

    for _ in range(3):
        event = get_raw_event()
        events.append(event)
        events_ids.add(event["id"])
        places_ids.add(event["place"]["id"])
        latest_changed_at = max(
            latest_changed_at,
            datetime.fromisoformat(event["changed_at"]).date(),
        )

    events_provider_client.kwargs["pages"] = {
        None: {"next": "abc123", "results": events[:2]},
        "abc123": {
            "next": None,
            "results": events[2:],
        },
    }

    await sync_service.sync()

    assert uow.sync_meta.meta.sync_status == SyncStatus.SYNCED
    assert uow.sync_meta.meta.last_changed_at == latest_changed_at
    assert uow.sync_meta.meta.last_sync_time <= get_datetime_now()
    assert set(uow.places.places.keys()) == places_ids
    assert set(uow.events.events.keys()) == events_ids
    assert uow.committed


@pytest.mark.parametrize("prev_status", [SyncStatus.NEVER, SyncStatus.SYNCED])
@pytest.mark.asyncio
async def test_sync_rollback_on_error(
    prev_status: SyncStatus, sync_service: SyncService, uow: FakeUnitOfWork
):
    meta = SyncMeta(id=1, sync_status=prev_status)
    uow.sync_meta = FakeSyncMetaRepository(meta=meta)
    sync_service._run_fetch = AsyncMock(side_effect=TimeoutError)

    await sync_service.sync()

    assert uow.sync_meta.meta.sync_status == prev_status
    assert uow.committed
