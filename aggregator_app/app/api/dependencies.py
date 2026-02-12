"""Зависимости API."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import db_manager
from app.services import EventsProviderClient, EventsService, TicketsService


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
