"""Репозиторий мест проведения событий."""

from collections.abc import Any

from app.orm.models import Place
from app.orm.repositories.base import BaseRepository


class PlaceRepository(BaseRepository):
    """Репозиторий мест проведения событий."""

    def add(self, json_data: dict[str, Any]) -> Place:
        """Добавить место проведения события."""
        obj = Place(**json_data)
        self._session.add(obj)
        return obj
