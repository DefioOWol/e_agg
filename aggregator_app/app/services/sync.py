"""Сервис синхронизации данных."""

import logging
from datetime import UTC, date, datetime

from aiohttp.client_exceptions import ClientResponseError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import db_manager
from app.orm.models import Event, Place, SyncMeta, SyncStatus
from app.orm.repositories import (
    EventRepository,
    PlaceRepository,
    SyncMetaRepository,
)
from app.services.events_provider import (
    EventsPaginator,
    EventsProviderClient,
    EventsProviderParser,
)

logging.basicConfig(level=logging.INFO, filename="app.log", filemode="w")
logger = logging.getLogger(__name__)


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
        logger.info("Инициализация задачи")

        async with db_manager.session() as session:
            sync_meta = await self._get_sync_meta(session)

            if sync_meta.sync_status == SyncStatus.PENDING:
                logger.info(
                    "Обнаружен статус %s, исправляем",
                    sync_meta.sync_status.value,
                )
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
        logger.info("Задача синхронизации добавлена в планировщик")

    def trigger_job(self):
        """Вызвать задачу синхронизации."""
        logger.info("Запрошен внеплановый запуск задачи")
        self._scheduler.modify_job(
            self.SYNC_JOB_ID,
            next_run_time=datetime.now(UTC),
        )

    async def _sync(self):
        """Синхронизировать данные."""
        logger.info("Начало синхронизации")

        async with db_manager.session() as session:
            sync_meta = await self._get_sync_meta(session)

            if (sync_status := sync_meta.sync_status) == SyncStatus.PENDING:
                logger.warning("Синхронизация уже выполняется, пропускаем")
                return

            sync_meta.sync_status = SyncStatus.PENDING
            await session.commit()

        logger.info(
            "Статус синхронизации установлен в '%s'",
            sync_meta.sync_status.value,
        )

        try:
            (
                event_data_list,
                place_data_list,
                latest_changed_at,
            ) = await self._run_fetch(sync_meta)
        except (TimeoutError, ClientResponseError) as e:
            logger.exception(
                "Ошибка при получении данных из API: [%d] %s",
                e.status,
                e.message,
            )
            await self._rollback_sync_meta(sync_status)
        else:
            await self._update_db(
                event_data_list, place_data_list, latest_changed_at
            )
            logger.info("Синхронизация завершена")

    async def _run_fetch(
        self, sync_meta: SyncMeta
    ) -> tuple[list[Event], list[Place], date]:
        """Загрузить данные из API."""
        latest_changed_at = sync_meta.last_changed_at or self.DEFAULT_CHANGED_AT
        logger.info(
            "Получение данных из API, начиная с %s",
            latest_changed_at.isoformat(),
        )

        async with EventsProviderClient() as client:
            event_data_dict = {}
            place_data_dict = {}

            parser = EventsProviderParser()
            paginator = EventsPaginator(client, latest_changed_at)

            async for event in paginator:
                event_data, place_data = parser.parse_event_dict(event)
                place_data_dict[place_data["id"]] = place_data
                event_data_dict[event_data["id"]] = event_data
                latest_changed_at = max(
                    latest_changed_at,
                    event_data["changed_at"].date(),
                )

        logger.info(
            "Получение завершено: events=%d, places=%d, latest_changed_at=%s",
            len(event_data_dict),
            len(place_data_dict),
            latest_changed_at.isoformat(),
        )

        event_data_list = list(event_data_dict.values())
        place_data_list = list(place_data_dict.values())
        return event_data_list, place_data_list, latest_changed_at

    async def _update_db(
        self,
        event_data_list: list[Event],
        place_data_list: list[Place],
        latest_changed_at: date,
    ):
        """Обновить базу данных."""
        logger.info(
            "Обновление БД: events=%d, places=%d",
            len(event_data_list),
            len(place_data_list),
        )

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

            logger.info("Метаданные обновлены: %s", str(sync_meta))
        logger.info("Обновление завершено")

    async def _rollback_sync_meta(self, prev_sync_status: SyncStatus):
        """Обработать ошибку синхронизации."""
        logger.info("Откатываем метаданные")

        async with db_manager.session() as session:
            sync_meta = await self._get_sync_meta(session)
            sync_meta.sync_status = prev_sync_status
            await session.commit()

        logger.info(
            "Статус синхронизации возвращен к '%s'", prev_sync_status.value
        )

    async def _get_sync_meta(self, session: AsyncSession) -> SyncMeta:
        """Получить метаданные синхронизации."""
        logger.info("Получаем метаданные")

        sync_meta_repo = SyncMetaRepository(session)
        sync_meta, _ = await sync_meta_repo.get_or_add(for_update=True)

        logger.info("Метаданные получены: %s", str(sync_meta))
        return sync_meta

    def _get_next_run_time(self, last_sync_time: datetime | None) -> datetime:
        """Получить следующее время запуска."""
        if last_sync_time is None:
            return datetime.now(UTC)
        return last_sync_time + self.SYNC_JOB_TRIGGER.interval


scheduler = AsyncIOScheduler(timezone=UTC)
