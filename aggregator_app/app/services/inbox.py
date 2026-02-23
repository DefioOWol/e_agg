"""Сервис идемпотентности."""

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.orm.db_manager import db_manager
from app.orm.uow import IUnitOfWork, SqlAlchemyUnitOfWork
from app.services.utils import scheduler

logger = logging.getLogger(__name__)


class InboxService:
    """Сервис идемпотентности."""

    INBOX_JOB_ID = "inbox-job"
    INBOX_JOB_TRIGGER = IntervalTrigger(seconds=settings.inbox_seconds_interval)

    def __init__(
        self,
        uow: IUnitOfWork,
        scheduler: AsyncIOScheduler,
    ):
        self._uow = uow
        self._scheduler = scheduler

    async def init_jobs(self):
        """Инициализировать задачу идемпотентности."""
        logger.info("Инициализация задачи обработки истекших ключей")

        self._scheduler.add_job(
            self.process_expired,
            trigger=self.INBOX_JOB_ID,
            id=self.INBOX_JOB_TRIGGER,
            max_instances=1,
            next_run_time=datetime.now(UTC),
        )

        logger.info("Задача обработки истекших ключей добавлена в планировщик")

    async def process_expired(self):
        """Обработать истекшие ключи."""
        logger.info("Обработка истекших ключей")

        async with self._uow as uow:
            deleted_count = await uow.inbox.delete_expired()
            uow.commit()

        logger.info("Удалено %d ключей", deleted_count)


def get_inbox_service() -> InboxService:
    return InboxService(
        SqlAlchemyUnitOfWork(db_manager),
        scheduler,
    )
