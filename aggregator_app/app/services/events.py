"""Сервис событий."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import EventFilter
from app.orm.models import Event
from app.orm.repositories import EventRepository


class EventsService:
    """Сервис событий."""

    def __init__(self, session: AsyncSession):
        self._event_repo = EventRepository(session)

    async def get_paginated(
        self, filter_: EventFilter, page: int, page_size: int | None
    ) -> tuple[list[Event], int]:
        """Получить погинированные события и общее количество."""
        stmt = select(Event)
        stmt = filter_.filter(stmt)
        items = await self._event_repo.get_paginated(
            stmt.order_by(Event.event_time, Event.id),
            page,
            page_size,
        )

        stmt = select(func.count()).select_from(Event)
        stmt = filter_.filter(stmt)
        count = await self._event_repo.get_select_scalar(stmt)

        return items, count
