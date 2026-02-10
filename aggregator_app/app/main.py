"""Основной модуль приложения."""

from contextlib import asynccontextmanager
from datetime import UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.api.routers import healthcheck
from app.orm.db_manager import db_manager
from app.services import SyncService

scheduler = AsyncIOScheduler(timezone=UTC)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения.

    Инициализирует сессию базы данных и сервис синхронизации
    и запускает планировщик.
    В конце жизненного цикла закрывает сессию базы данных
    и останавливает планировщик.

    """
    await db_manager.init()
    await SyncService(scheduler).init_job()
    scheduler.start()
    yield
    scheduler.shutdown()
    await db_manager.close()


app = FastAPI(
    title="Events aggregator API",
    description="API for events aggregator",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api",
)

app.include_router(healthcheck.router)
