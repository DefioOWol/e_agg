"""Репозиторий идемпотентности."""

from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import delete

from app.orm.models import Inbox
from app.orm.repositories.base import BaseRepository


class IInboxRepository(Protocol):
    """Интерфейс репозитория идемпотентности."""

    async def get(self, key: str) -> Inbox | None:
        """Получить идемпотентность по ключу."""

    def create(
        self, key: str, request_hash: str, response: dict[str, Any]
    ) -> Inbox:
        """Создать идемпотентность."""

    async def delete_expired(self) -> int:
        """Удалить истекшие ключи."""


class InboxRepository(BaseRepository, IInboxRepository):
    """Репозиторий идемпотентности."""

    async def get(self, key: str) -> Inbox | None:
        return await self._session.get(Inbox, key)

    def create(
        self, key: str, request_hash: str, response: dict[str, Any]
    ) -> Inbox:
        inbox = Inbox(
            key=key,
            request_hash=request_hash,
            response=response,
        )
        self._session.add(inbox)
        return inbox

    async def delete_expired(self) -> int:
        stmt = delete(Inbox).where(Inbox.expires_at <= datetime.now(UTC))
        result = await self._session.execute(stmt)
        return result.rowcount
