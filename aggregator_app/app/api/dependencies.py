"""Зависимости API."""

from collections.abc import AsyncGenerator
from datetime import date
from typing import Annotated

from fastapi import Depends
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import db_manager
from app.orm.models import Event
from app.services import EventsProviderClient, EventsService, TicketsService


class EventFilter(Filter):
    """Фильтр событий.

    Атрибуты:
    - `event_time__gte`: date | None - Дата начала события в ISO формате;
        может быть пустым; синоним - date_from.

    """

    event_time__gte: date | None = Field(None, alias="date_from")

    @field_validator("event_time__gte")
    @classmethod
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


async def get_events_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventsService:
    """Получить сервис событий."""
    return EventsService(session, EventsProviderClient())


async def get_tickets_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TicketsService:
    """Получить сервис регистрации."""
    return TicketsService(session, EventsProviderClient())
