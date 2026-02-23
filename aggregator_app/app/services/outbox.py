"""Сервис очереди событий."""

import logging
from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.orm.db_manager import db_manager
from app.orm.models import Outbox, OutboxStatus
from app.orm.uow import IUnitOfWork, SqlAlchemyUnitOfWork
from app.services.notification import (
    CapashinoNotificationClient,
    INotificationClient,
)
from app.services.utils import scheduler, with_external_client

logger = logging.getLogger(__name__)


class OutboxService:
    """Сервис очереди событий."""

    OUTBOX_JOB_ID = "outbox-job"
    OUTBOX_JOB_TRIGGER = IntervalTrigger(
        seconds=settings.outbox_seconds_interval
    )

    def __init__(
        self,
        uow: IUnitOfWork,
        scheduler: AsyncIOScheduler,
        client: INotificationClient,
    ):
        self._uow = uow
        self._scheduler = scheduler
        self._client = client

    async def init_jobs(self):
        """Инициализировать задачу очереди событий."""
        logger.info("Инициализация задачи очереди событий")

        self._scheduler.add_job(
            self.process_waiting,
            trigger=self.OUTBOX_JOB_TRIGGER,
            id=self.OUTBOX_JOB_ID,
            max_instances=1,
            next_run_time=datetime.now(UTC),
        )

        logger.info("Задача очереди событий добавлена в планировщик")

    async def process_waiting(self):
        """Обработать ожидающие события."""
        logger.info("Обработка ожидающих событий")

        successful_processed = 0
        async with self._uow as uow:
            outbox = await uow.outbox.get_waiting(for_update=True)

            for item in outbox:
                successful_processed += await with_external_client(
                    self._client,
                    self._process_notify,
                    func_kwargs={"item": item},
                    on_success=self._update_status,
                    on_success_kwargs={"uow": uow, "item": item},
                    on_error=self._handle_error,
                )

        logger.info(
            "Успешно обработано %d/%d ожидающих событий",
            successful_processed,
            len(outbox),
        )

    async def _process_notify(
        self, client: INotificationClient, item: Outbox
    ) -> dict[str, Any]:
        """Обработать событие регистрации билета."""
        return await client.notify(item)

    async def _update_status(
        self, _: None, uow: IUnitOfWork, item: Outbox
    ) -> bool:
        """Обновить статус события в очереди на отправленное."""
        await uow.outbox.update_status(item.id, OutboxStatus.SENT)
        await uow.commit()
        return True

    async def _handle_error(self, e: Exception) -> bool:
        """Обработать ошибку внешнего API."""
        message = (
            f"{getattr(e, 'status', 'XXX')}"
            f" {getattr(e, 'message', 'Unknown error')}"
        )
        logger.exception("Ошибка при обработке события в очереди: %s", message)
        return False


def get_outbox_service() -> OutboxService:
    return OutboxService(
        SqlAlchemyUnitOfWork(db_manager),
        scheduler,
        CapashinoNotificationClient(),
    )
