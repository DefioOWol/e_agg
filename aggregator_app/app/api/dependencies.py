"""Зависимости API."""

from collections.abc import AsyncGenerator
from datetime import date

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import db_manager
from app.orm.models import Event


class EventFilter(Filter):
    """Фильтр событий."""

    event_time__gte: date | None = Field(None, alias="date_from")

    @field_validator("event_time__gte")
    def string_to_date(cls, v):
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    class Constants(Filter.Constants):
        model = Event

    class Config:
        validate_by_name = True


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить сессию БД."""
    async with db_manager.session() as session:
        yield session
