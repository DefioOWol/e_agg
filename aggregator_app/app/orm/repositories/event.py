"""Репозиторий событий."""

from collections.abc import Any
from uuid import UUID

from app.orm.models import Event
from app.orm.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """Репозиторий событий."""

    def add(self, json_data: dict[str, Any], place_id: UUID) -> Event:
        """Добавить событие."""
        obj = Event(**json_data | {"place_id": place_id})
        self._session.add(obj)
        return obj
