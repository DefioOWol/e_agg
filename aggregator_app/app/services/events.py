"""Сервис событий."""

from uuid import UUID

from cashews import cache
from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.api.filters import EventFilter
from app.orm.models import Event
from app.orm.uow import IUnitOfWork
from app.services.events_provider import (
    EventsProviderClient,
    with_events_provider,
)


class EventsService:
    """Сервис событий."""

    def __init__(
        self,
        uow: IUnitOfWork,
        client: EventsProviderClient,
    ):
        self._uow = uow
        self._client = client

    async def get_paginated(
        self, filter_: EventFilter, page: int, page_size: int | None
    ) -> tuple[list[Event], int]:
        """Получить погинированные события и общее количество.

        Аргументы:
        - `filter_`: `EventFilter` - Фильтр событий.
        - `page` - Номер страницы.
        - `page_size` - Размер страницы.

        Возвращает:
        - Пагинированный список событий и общее количество событий.

        """
        async with self._uow as uow:
            stmt = select(Event)
            stmt = filter_.filter(stmt)
            events = await uow.events.get_paginated(
                stmt.order_by(Event.event_time, Event.id),
                page,
                page_size,
            )

            stmt = select(func.count()).select_from(Event)
            stmt = filter_.filter(stmt)
            count = await uow.events.get_select_scalar(stmt)

            return events, count

    async def get_by_id(self, event_id: UUID) -> Event | None:
        """Получить событие по ID."""
        async with self._uow as uow:
            stmt = select(Event).where(Event.id == event_id)
            return await uow.events.get_select_scalar(stmt)

    @cache(ttl="30s", key="event_seats:{event_id}")
    async def get_seats(self, event_id: UUID) -> list[str]:
        """Получить свободные места на событии.

        Ответ кешируется на 30 секунд по ключу `event_seats:{event_id}`.

        """
        return await with_events_provider(
            self._client,
            self._fetch_seats,
            func_kwargs={"event_id": event_id},
            on_error=self._raise_server_error,
        )

    async def _fetch_seats(
        self, client: EventsProviderClient, event_id: UUID
    ) -> list[str]:
        """Получить свободные места на событии."""
        result = await client.get_seats(event_id)
        return result["seats"]

    async def _raise_server_error(self, _: Exception):
        """Вызвать ошибку сервера."""
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
