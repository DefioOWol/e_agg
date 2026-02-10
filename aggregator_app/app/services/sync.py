"""Сервис синхронизации данных."""

from datetime import UTC, date, datetime
from typing import Any

from aiohttp import ClientTimeout
from aiohttp.client_exceptions import ClientResponseError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import db_manager
from app.orm.models import Base, Event, Place, SyncMeta, SyncStatus
from app.orm.repositories import (
    EventRepository,
    PlaceRepository,
    SyncMetaRepository,
)
from app.services.events_provider import EventsPaginator, EventsProviderClient


class SyncService:
    """Сервис синхронизации данных."""

    DEFAULT_CHANGED_AT = date(2000, 1, 1)

    SYNC_JOB_ID = "sync-events"
    SYNC_JOB_TRIGGER = IntervalTrigger(days=1)

    def __init__(self, scheduler: AsyncIOScheduler):
        """Инициализировать сервис синхронизации."""
        self._scheduler = scheduler

    async def init_job(self):
        """Инициализировать задачу синхронизации."""
        async with db_manager.session() as session:
            sync_meta = await self._get_sync_meta(session)
            if sync_meta.sync_status == SyncStatus.PENDING:
                sync_meta.sync_status = (
                    SyncStatus.NEVER
                    if sync_meta.last_sync_time is None
                    else SyncStatus.SYNCED
                )
            await session.commit()

        self._scheduler.add_job(
            self._sync,
            trigger=self.SYNC_JOB_TRIGGER,
            id=self.SYNC_JOB_ID,
            max_instances=1,
            next_run_time=self._get_next_run_time(sync_meta.last_sync_time),
        )

    def trigger_job(self):
        """Вызвать задачу синхронизации."""
        self._scheduler.scheduled_job(
            self.SYNC_JOB_TRIGGER,
            id=self.SYNC_JOB_ID,
            max_instances=1,
            next_run_time=datetime.now(UTC),
        )

    def _get_next_run_time(self, last_sync_time: datetime | None) -> datetime:
        """Получить следующее время запуска."""
        if last_sync_time is None:
            return datetime.now(UTC)
        return last_sync_time + self.SYNC_JOB_TRIGGER.interval

    async def _sync(self):
        """Синхронизировать данные."""
        async with db_manager.session() as session:
            sync_meta = await self._get_sync_meta(session)
            if (sync_status := sync_meta.sync_status) == SyncStatus.PENDING:
                return
            sync_meta.sync_status = SyncStatus.PENDING
            await session.commit()

        try:
            (
                event_data_list,
                place_data_list,
                latest_changed_at,
            ) = await self._run_fetch(sync_meta)
        except (ClientTimeout, ClientResponseError):
            await self._rollback_sync_meta(sync_status)
        else:
            await self._update_db(
                event_data_list, place_data_list, latest_changed_at
            )

    async def _get_sync_meta(self, session: AsyncSession) -> SyncMeta:
        """Получить метаданные синхронизации."""
        sync_meta_repo = SyncMetaRepository(session)
        sync_meta, _ = await sync_meta_repo.get_or_add(for_update=True)
        return sync_meta

    async def _run_fetch(
        self, sync_meta: SyncMeta
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], date]:
        """Загрузить данные из API."""
        async with EventsProviderClient() as client:
            latest_changed_at = (
                sync_meta.last_changed_at or self.DEFAULT_CHANGED_AT
            )
            paginator = EventsPaginator(client, latest_changed_at)

            event_data_list = []
            place_data_list = []
            async for event in paginator:
                place = event.pop("place")
                self._normalize_datetime(place, Place)
                self._normalize_datetime(event, Event)

                place_data_list.append(place)
                event_data_list.append(event | {"place_id": place["id"]})
                latest_changed_at = max(
                    latest_changed_at,
                    event["changed_at"].date(),
                )

        return event_data_list, place_data_list, latest_changed_at

    async def _update_db(
        self,
        event_data_list: list[dict[str, Any]],
        place_data_list: list[dict[str, Any]],
        latest_changed_at: date,
    ):
        """Обновить базу данных."""
        async with db_manager.session() as session:
            event_repo = EventRepository(session)
            place_repo = PlaceRepository(session)

            async with session.begin():
                await place_repo.upsert(place_data_list)
                await event_repo.upsert(event_data_list)

                sync_meta = await self._get_sync_meta(session)
                sync_meta.sync_status = SyncStatus.SYNCED
                sync_meta.last_sync_time = datetime.now(UTC)
                sync_meta.last_changed_at = latest_changed_at

    async def _rollback_sync_meta(self, prev_sync_status: SyncStatus):
        """Обработать ошибку синхронизации."""
        async with db_manager.session() as session:
            sync_meta = await self._get_sync_meta(session)
            sync_meta.sync_status = prev_sync_status
            await session.commit()

    def _normalize_datetime(
        self, data: dict[str, Any], cls_: type[Base]
    ) -> dict[str, Any]:
        """Нормализовать даты в данных."""
        for c in cls_.__table__.c:
            if isinstance(c.type, DateTime):
                data[c.key] = datetime.fromisoformat(data[c.key]).astimezone(
                    UTC
                )
        return data
