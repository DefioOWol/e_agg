"""Сервис событий."""

from uuid import UUID

from cashews import cache
from fastapi import HTTPException, status
from fastapi_filter.contrib.sqlalchemy import Filter

from app.orm.models import Event
from app.orm.uow import IUnitOfWork
from app.services.events_provider import (
    IEventsProviderClient,
)
from app.services.utils import with_external_client


class EventsService:
    """Сервис событий."""

    def __init__(
        self,
        uow: IUnitOfWork,
        client: IEventsProviderClient,
    ):
        self._uow = uow
        self._client = client

    async def get_paginated(
        self, filter_: Filter, page: int, page_size: int | None
    ) -> tuple[list[Event], int]:
        """Получить погинированные события и общее количество.

        Аргументы:
        - `filter_` - Фильтр событий.
        - `page` - Номер страницы.
        - `page_size` - Размер страницы.

        Возвращает:
        - Пагинированный список событий и общее количество событий.

        """
        async with self._uow as uow:
            events = await uow.events.get_paginated(page, page_size, filter_)
            count = await uow.events.get_count(filter_)
        return events, count

    async def get_by_id(self, event_id: UUID) -> Event | None:
        """Получить событие по ID."""
        async with self._uow as uow:
            return await uow.events.get_by_id(event_id)

    @cache(ttl="30s", key="event_seats:{event_id}")
    async def get_seats(self, event_id: UUID) -> list[str]:
        """Получить свободные места на событии.

        Ответ кешируется на 30 секунд по ключу `event_seats:{event_id}`.

        """
        return await with_external_client(
            self._client,
            self._fetch_seats,
            func_kwargs={"event_id": event_id},
            on_error=self._raise_server_error,
        )

    async def _fetch_seats(
        self, client: IEventsProviderClient, event_id: UUID
    ) -> list[str]:
        """Получить свободные места на событии."""
        result = await client.get_seats(event_id)
        return result["seats"]

    async def _raise_server_error(self, _: Exception):
        """Вызвать ошибку сервера."""
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
