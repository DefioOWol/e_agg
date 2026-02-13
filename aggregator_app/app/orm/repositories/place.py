"""Репозиторий мест проведения событий."""

from typing import Any, Protocol

from sqlalchemy.dialects.postgresql import insert

from app.orm.models import Place
from app.orm.repositories.base import BaseRepository


class IPlaceRepository(Protocol):
    """Интерфейс репозитория мест проведения."""

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        """Вставить или обновить записи при конфликте.

        Данные должны быть в виде словаря с ключами,
        соответсвующими полям модели `Place`, и приведенными
        к требуемым типам данных значениями.

        """


class PlaceRepository(BaseRepository, IPlaceRepository):
    """Репозиторий мест проведения событий.

    Реализует `IPlaceRepository`.

    """

    async def upsert(self, json_data_list: list[dict[str, Any]]):
        stmt = insert(Place).values(json_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Place.id],
            set_={c.key: c for c in stmt.excluded if not c.primary_key},
        )
        await self._session.execute(stmt)
