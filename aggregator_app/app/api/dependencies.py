"""Зависимости API."""

from collections.abc import AsyncGenerator
from datetime import date

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import db_manager
from app.orm.models import Event


class EventFilter(Filter):
    """Фильтр событий."""

    event_time__gte: date | None = Field(None, alias="date_from")

    class Constants(Filter.Constants):
        model = Event


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить сессию БД."""
    async with db_manager.session() as session:
        yield session
