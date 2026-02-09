"""Репозиторий метаданных синхронизации."""

from collections.abc import Any

from sqlalchemy import select, update

from app.orm.models import SyncMeta
from app.orm.repositories.base import BaseRepository


class SyncMetaRepository(BaseRepository):
    """Репозиторий метаданных синхронизации."""

    async def get_or_add(
        self, for_update: bool = False
    ) -> tuple[SyncMeta, bool]:
        """Получить или добавить метаданные синхронизации."""
        stmt = select(SyncMeta).where(SyncMeta.id == 1)
        if for_update:
            stmt = stmt.with_for_update()
        obj = (await self._session.execute(stmt)).scalar_one_or_none()
        if is_new := obj is None:
            obj = SyncMeta(id=1)
            self._session.add(obj)
        return obj, is_new

    async def update(self, json_data: dict[str, Any]) -> SyncMeta:
        """Обновить метаданные синхронизации."""
        stmt = (
            update(SyncMeta)
            .where(SyncMeta.id == 1)
            .values(**json_data)
            .returning(SyncMeta)
        )
        return (await self._session.execute(stmt)).scalar_one()
