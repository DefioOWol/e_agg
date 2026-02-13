"""Репозиторий событий."""

from typing import Any, Protocol

from sqlalchemy import Select
from sqlalchemy.dialects.postgresql import insert

from app.orm.models import Event
from app.orm.repositories.base import BaseRepository


class IEventRepository(Protocol):
    """Интерфейс репозитория событий."""

    async def get_paginated(
        self, stmt: Select, page: int, page_size: int | None
    ) -> list[Event]:
        """Получить пагинированные события по запросу.

        Аргументы:
        - `stmt`: Select - Обрабатываемый запрос на получение данных.
        - `page` - Номер страницы.
        - `page_size`: int | None - Размер страницы;
            при None пагинация не выполняется.

        Возвращает:
        - list[Event] - Список событий.

        """

    async def get_select_scalar(self, stmt: Select) -> Any:
        """Получить скалярное значение по select-запросу."""

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
        self, stmt: Select, page: int, page_size: int | None
    ) -> list[Event]:
        if page_size:
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_select_scalar(self, stmt: Select) -> Any:
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        stmt = insert(Event).values(json_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Event.id],
            set_={c.key: c for c in stmt.excluded if not c.primary_key},
        )
        await self._session.execute(stmt)
