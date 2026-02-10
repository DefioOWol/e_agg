"""Репозиторий событий."""

from typing import Any

from sqlalchemy.dialects.postgresql import insert

from app.orm.models import Event
from app.orm.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """Репозиторий событий."""

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        stmt = insert(Event).values(json_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Event.id],
            set_={c.key: c for c in stmt.excluded if not c.primary_key},
        )
        await self._session.execute(stmt)
