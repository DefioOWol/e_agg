"""Репозиторий очереди событий."""

from typing import Any, Protocol

from sqlalchemy import select, update

from app.orm.models import Outbox, OutboxStatus, OutboxType
from app.orm.repositories.base import BaseRepository


class IOutboxRepository(Protocol):
    """Интерфейс репозитория очереди событий."""

    def create(self, type_: OutboxType, payload: dict[str, Any]) -> Outbox:
        """Создать событие в очереди."""

    async def get_waiting(self, *, for_update: bool = False) -> list[Outbox]:
        """Получить ожидающие события."""

    async def update_status(self, id: int, status: OutboxStatus) -> bool:
        """Обновить статус события в очереди."""


class OutboxRepository(BaseRepository, IOutboxRepository):
    """Репозиторий очереди событий."""

    def create(self, type_: OutboxType, payload: dict[str, Any]) -> Outbox:
        outbox = Outbox(type=type_, payload=payload)
        self._session.add(outbox)
        return outbox

    async def get_waiting(self, *, for_update: bool = False) -> list[Outbox]:
        stmt = select(Outbox).where(Outbox.status == OutboxStatus.WAITING)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, id: int, status: OutboxStatus) -> bool:
        stmt = update(Outbox).where(Outbox.id == id).values(status=status)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)
