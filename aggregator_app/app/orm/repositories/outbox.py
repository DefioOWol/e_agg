"""Репозиторий очереди событий."""

from typing import Any, Protocol

from sqlalchemy import select, update

from app.orm.models import Outbox, OutboxStatus
from app.orm.repositories.base import BaseRepository


class IOutboxRepository(Protocol):
    """Интерфейс репозитория очереди событий."""

    async def create(self, payload: dict[str, Any]) -> Outbox:
        """Создать событие в очереди."""

    async def get_waiting(self) -> list[Outbox]:
        """Получить ожидающие события."""

    async def update_status(self, id: int, status: OutboxStatus) -> bool:
        """Обновить статус события в очереди."""


class OutboxRepository(BaseRepository, IOutboxRepository):
    """Репозиторий очереди событий."""

    async def create(self, payload: dict[str, Any]) -> Outbox:
        outbox = Outbox(**payload)
        self._session.add(outbox)
        return outbox

    async def get_waiting(self) -> list[Outbox]:
        stmt = select(Outbox).where(Outbox.status == OutboxStatus.WAITING)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, id: int, status: OutboxStatus) -> bool:
        stmt = update(Outbox).where(Outbox.id == id).values(status=status)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)
