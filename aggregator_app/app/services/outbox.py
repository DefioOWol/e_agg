"""Сервис очереди событий."""

import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.orm.db_manager import db_manager
from app.orm.models import Outbox, OutboxStatus, OutboxType
from app.orm.uow import IUnitOfWork, SqlAlchemyUnitOfWork
from app.services.utils import scheduler, with_external_client

logger = logging.getLogger(__name__)


class OutboxService:
    """Сервис очереди событий."""

    OUTBOX_JOB_ID = "outbox-job"
    OUTBOX_JOB_TRIGGER = IntervalTrigger(hours=1)

    def __init__(self, uow: IUnitOfWork, scheduler: AsyncIOScheduler, client):
        self._uow = uow
        self._scheduler = scheduler
        self._client = client

    def init_job(self):
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

        async with self._uow as uow:
            outbox = await uow.outbox.get_waiting(for_update=True)

            for item in outbox:
                match item.type:
                    case OutboxType.TICKET_REGISTER:
                        await with_external_client(
                            self._client,
                            self._process_ticket_register,
                            func_kwargs={"item": item},
                            on_success=self._update_status,
                            on_success_kwargs={"uow": uow, "item": item},
                            on_error=self._handle_error,
                        )

        logger.info("Обработка ожидающих событий завершена")

    async def _process_ticket_register(self, client, item: Outbox):
        """Обработать событие регистрации билета."""
        raise TimeoutError

    async def _update_status(self, _: None, uow: IUnitOfWork, item: Outbox):
        """Обновить статус события в очереди на отправленное."""
        await uow.outbox.update_status(item.id, OutboxStatus.SENT)
        await uow.commit()

    async def _handle_error(self, e: Exception):
        """Обработать ошибку внешнего API."""
        logger.exception("Ошибка при обработке события в очереди: %s", str(e))


def get_outbox_service() -> OutboxService:
    return OutboxService(
        SqlAlchemyUnitOfWork(db_manager),
        scheduler,
        MagicMock(),
    )
