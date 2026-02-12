"""Репозиторий метаданных синхронизации."""

from sqlalchemy import select

from app.orm.models import SyncMeta, SyncStatus
from app.orm.repositories.base import BaseRepository


class SyncMetaRepository(BaseRepository):
    """Репозиторий метаданных синхронизации."""

    async def get_or_add(
        self, *, for_update: bool = False
    ) -> tuple[SyncMeta, bool]:
        """Получить или добавить метаданные синхронизации.

        Аргументы:
        - `for_update`: bool - флаг блокировки чтения для обновления;
            по умолчанию False.

        Возвращает:
        - tuple[SyncMeta, bool] - объект метаданных и статус создания записи.

        """
        stmt = select(SyncMeta).where(SyncMeta.id == 1)
        if for_update:
            stmt = stmt.with_for_update()
        obj = (await self._session.execute(stmt)).scalar_one_or_none()
        if is_new := obj is None:
            obj = SyncMeta(id=1, sync_status=SyncStatus.NEVER)
            self._session.add(obj)
        return obj, is_new
