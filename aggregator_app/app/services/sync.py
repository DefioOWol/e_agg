"""Сервис синхронизации данных."""

import logging
from datetime import UTC, date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.orm.db_manager import db_manager
from app.orm.models import Event, Place, SyncMeta, SyncStatus
from app.orm.uow import IUnitOfWork, SqlAlchemyUnitOfWork
from app.services.events_provider import (
    EventsPaginator,
    EventsProviderClient,
    EventsProviderParser,
    IEventsProviderClient,
    with_events_provider,
)

logging.basicConfig(level=logging.INFO, filename="app.log", filemode="w")
logger = logging.getLogger(__name__)


class SyncService:
    """Сервис синхронизации данных."""

    DEFAULT_CHANGED_AT = date(2000, 1, 1)

    SYNC_JOB_ID = "sync-events"
    SYNC_JOB_TRIGGER = IntervalTrigger(days=1)

    def __init__(
        self,
        uow: IUnitOfWork,
        scheduler: AsyncIOScheduler,
        client: IEventsProviderClient,
        paginator: EventsPaginator,
        parser: EventsProviderParser,
    ):
        """Инициализировать сервис синхронизации."""
        self._uow = uow
        self._scheduler = scheduler
        self._client = client
        self._paginator = paginator
        self._parser = parser

    async def init_job(self):
        """Инициализировать задачу синхронизации.

        В начале работы проверяется статус синхронизации и если он равен
        `PENDING`, то исправляется на другой. Это сделано из расчета
        одной реплики сервиса и того, что она может упасть в любой момент.

        Затем задача добавляется в планировщик на основе метаданных.

        """
        logger.info("Инициализация задачи")

        async with self._uow as uow:
            sync_meta = await self._get_sync_meta(uow)

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
            await uow.commit()

        self._scheduler.add_job(
            self.sync,
            trigger=self.SYNC_JOB_TRIGGER,
            id=self.SYNC_JOB_ID,
            max_instances=1,
            next_run_time=self._get_next_run_time(sync_meta.last_sync_time),
        )
        logger.info("Задача синхронизации добавлена в планировщик")

    def _get_next_run_time(self, last_sync_time: datetime | None) -> datetime:
        """Получить следующее время запуска по предыдущему."""
        if last_sync_time is None:
            return datetime.now(UTC)
        return last_sync_time + self.SYNC_JOB_TRIGGER.interval

    def trigger_job(self):
        """Задать внеплановый запуск задачи синхронизации.

        Не вызывает синхронизацию напрямую, но говорит планировщику
        начать ее как можно раньше. Если синхронизация уже идет, то
        данный вызов не повлияет на нее, однако произойдет повторный
        запуск после завершения первой.

        """
        logger.info("Запрошен внеплановый запуск задачи")
        self._scheduler.modify_job(
            self.SYNC_JOB_ID,
            next_run_time=datetime.now(UTC),
        )

    async def sync(self):
        """Основная функция синхронизации.

        В начале устанавливается статус `PENDING` в одной сессии.
        Если статус уже в этом состоянии, то функция не выполняется.
        Это необходимо, если было бы несколько реплик.

        Затем вызывается получение данных из внешнего API.
        При успехе в новой сессии одной транзакцией данные
        добавляются/обновляются, при ошибке - откатываются метаданные.

        """
        logger.info("Начало синхронизации")

        async with self._uow as uow:
            sync_meta = await self._get_sync_meta(uow)

            if (sync_status := sync_meta.sync_status) == SyncStatus.PENDING:
                logger.warning("Синхронизация уже выполняется, пропускаем")
                return

            sync_meta.sync_status = SyncStatus.PENDING
            await uow.commit()

        logger.info(
            "Статус синхронизации установлен в '%s'",
            sync_meta.sync_status.value,
        )

        await with_events_provider(
            self._client,
            self._run_fetch,
            func_kwargs={"sync_meta": sync_meta},
            on_success=self._update_db,
            on_error=self._rollback_sync_meta,
            on_error_kwargs={"prev_sync_status": sync_status},
        )

    async def _get_sync_meta(self, uow: IUnitOfWork) -> SyncMeta:
        """Получить метаданные синхронизации с блокировкой обновления."""
        logger.info("Получаем метаданные")

        sync_meta, _ = await uow.sync_meta.get_or_add(for_update=True)

        logger.info("Метаданные получены: %s", str(sync_meta))
        return sync_meta

    async def _run_fetch(
        self, client: IEventsProviderClient, sync_meta: SyncMeta
    ) -> tuple[list[Event], list[Place], date]:
        """Загрузить данные из API.

        Данные собираются в словари, так как одно и то же место проведения
        может присутствовать в разных событиях, а дубликаты не допускаются
        для on_conflict_do_update. Сбор происходит целиком, так как
        данных получаем сравнительно мало.

        """
        latest_changed_at = sync_meta.last_changed_at or self.DEFAULT_CHANGED_AT
        logger.info(
            "Получение данных из API, начиная с %s",
            latest_changed_at.isoformat(),
        )

        event_data_dict = {}
        place_data_dict = {}

        async for event in self._paginator(client, latest_changed_at):
            event_data, place_data = self._parser.parse_event_dict(event)
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
        self, fetch_result: tuple[list[Event], list[Place], date]
    ):
        """Обновить базу данных и метаданные.

        Для обновления создается новая сессия, так как держать одну
        сессию открытой на все время синхронизации не практично.
        Затем через upsert вставляются/обновляются данные о местах
        проведения и событиях.

        """
        logger.info(
            "Обновление БД: events=%d, places=%d",
            len(fetch_result[0]),
            len(fetch_result[1]),
        )

        async with self._uow as uow:
            async with uow.begin():
                await uow.places.upsert(fetch_result[1])
                await uow.events.upsert(fetch_result[0])

                sync_meta = await self._get_sync_meta(uow)
                sync_meta.sync_status = SyncStatus.SYNCED
                sync_meta.last_sync_time = datetime.now(UTC)
                sync_meta.last_changed_at = fetch_result[2]

            logger.info("Метаданные обновлены: %s", str(sync_meta))
        logger.info("Синхронизация завершена")

    async def _rollback_sync_meta(
        self, e: Exception, prev_sync_status: SyncStatus
    ):
        """Откатить метаданные до предыдущего статуса."""
        logger.exception("Ошибка при получении данных из API: %s", str(e))
        logger.info("Откатываем метаданные")

        async with self._uow as uow:
            sync_meta = await self._get_sync_meta(uow)
            sync_meta.sync_status = prev_sync_status
            await uow.commit()

        logger.info(
            "Статус синхронизации возвращен к '%s'", prev_sync_status.value
        )


scheduler = AsyncIOScheduler(timezone=UTC)


def get_sync_service() -> SyncService:
    return SyncService(
        SqlAlchemyUnitOfWork(db_manager),
        scheduler,
        EventsProviderClient(),
        EventsPaginator(),
        EventsProviderParser(),
    )
