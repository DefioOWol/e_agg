"""Репозиторий событий."""

from typing import Any, Protocol
from uuid import UUID

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.orm.models import Event
from app.orm.repositories.base import BaseRepository


class IEventRepository(Protocol):
    """Интерфейс репозитория событий."""

    async def get_paginated(
        self, page: int, page_size: int | None, filter_: Filter | None = None
    ) -> list[Event]:
        """Получить пагинированные события по запросу.

        Аргументы:
        - `page` - Номер страницы.
        - `page_size` - Размер страницы;
            при None пагинация не выполняется.
        - `filter_` - Фильтр событий; по умолчанию None.

        Возвращает:
        - list[Event] - Список событий.

        """

    async def get_by_id(self, event_id: UUID) -> Event | None:
        """Получить событие по ID."""

    async def get_count(self, filter_: Filter | None = None) -> int:
        """Получить количество событий."""

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        """Вставить или обновить записи при конфликте.

        Данные должны быть в виде словаря с ключами,
        соответсвующими полям модели `Event`, и приведенными
        к требуемым типам данных значениями.

        """


class EventRepository(BaseRepository, IEventRepository):
    """Репозиторий событий.

    Реализует `IEventRepository`.

    """

    async def get_paginated(
        self, page: int, page_size: int | None, filter_: Filter | None = None
    ) -> list[Event]:
        stmt = select(Event)
        if filter_:
            stmt = filter_.filter(stmt)
        stmt = stmt.order_by(Event.event_time, Event.id)
        if page_size:
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, event_id: UUID) -> Event | None:
        stmt = select(Event).where(Event.id == event_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_count(self, filter_: Filter | None = None) -> int:
        stmt = select(func.count()).select_from(Event)
        if filter_:
            stmt = filter_.filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        stmt = insert(Event).values(json_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Event.id],
            set_={c.key: c for c in stmt.excluded if not c.primary_key},
        )
        await self._session.execute(stmt)
