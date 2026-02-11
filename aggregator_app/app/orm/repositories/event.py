"""Репозиторий событий."""

from typing import Any

from sqlalchemy import Select
from sqlalchemy.dialects.postgresql import insert

from app.orm.models import Event
from app.orm.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """Репозиторий событий."""

    async def get_paginated(
        self, stmt: Select, page: int, page_size: int | None
    ) -> list[Event]:
        """Получить пагинированные события по запросу."""
        if page_size:
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_select_scalar(self, stmt: Select) -> Any:
        """Получить скалярное значение по запросу."""
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        """Вставить или обновить записи при конфликте."""
        stmt = insert(Event).values(json_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Event.id],
            set_={c.key: c for c in stmt.excluded if not c.primary_key},
        )
        await self._session.execute(stmt)
