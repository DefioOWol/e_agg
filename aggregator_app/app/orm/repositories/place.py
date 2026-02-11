"""Репозиторий мест проведения событий."""

from typing import Any

from sqlalchemy.dialects.postgresql import insert

from app.orm.models import Place
from app.orm.repositories.base import BaseRepository


class PlaceRepository(BaseRepository):
    """Репозиторий мест проведения событий."""

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        """Вставить или обновить записи при конфликте."""
        stmt = insert(Place).values(json_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Place.id],
            set_={c.key: c for c in stmt.excluded if not c.primary_key},
        )
        await self._session.execute(stmt)
