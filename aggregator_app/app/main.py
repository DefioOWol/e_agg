"""Основной модуль приложения."""

from contextlib import asynccontextmanager

from cashews import cache
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.routers import events, healthcheck, sync, tickets
from app.error_handlers import validation_exception_handler
from app.orm.db_manager import db_manager
from app.services.sync import get_sync_service
from app.services.utils import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения.

    Инициализирует сессию базы данных, сервис синхронизации,
    запускает планировщик, инициализирует кэш в памяти.
    В конце жизненного цикла завершает необходимые элементы.

    """
    await db_manager.init()
    await get_sync_service().init_job()
    scheduler.start()
    cache.setup("mem://")
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
app.include_router(sync.router)
app.include_router(events.router)
app.include_router(tickets.router)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
