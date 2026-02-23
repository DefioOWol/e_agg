"""Unit of Work."""

from collections.abc import AsyncGenerator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.db_manager import DBManager
from app.orm.repositories.event import EventRepository, IEventRepository
from app.orm.repositories.inbox import IInboxRepository, InboxRepository
from app.orm.repositories.member import IMemberRepository, MemberRepository
from app.orm.repositories.outbox import IOutboxRepository, OutboxRepository
from app.orm.repositories.place import IPlaceRepository, PlaceRepository
from app.orm.repositories.sync_meta import (
    ISyncMetaRepository,
    SyncMetaRepository,
)


class IUnitOfWork(AbstractAsyncContextManager[Self], Protocol):
    """Интерфейс Unit of Work."""

    events: IEventRepository
    places: IPlaceRepository
    members: IMemberRepository
    sync_meta: ISyncMetaRepository
    outbox: IOutboxRepository
    inbox: IInboxRepository

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[Self, None]:
        """Начать транзакцию."""

    async def commit(self):
        """Зафиксировать транзакцию."""

    async def rollback(self):
        """Откатить транзакцию."""


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """Реализация Unit of Work на основе SQLAlchemy.

    Реализует `IUnitOfWork`.

    """

    def __init__(self, manager: DBManager):
        self._manager = manager
        self._session_cm: AbstractAsyncContextManager | None = None
        self._session: AsyncSession | None = None

    async def __aenter__(self):
        self._session_cm = self._manager.session()
        self._session = await self._session_cm.__aenter__()

        self.events = EventRepository(self._session)
        self.places = PlaceRepository(self._session)
        self.members = MemberRepository(self._session)
        self.sync_meta = SyncMetaRepository(self._session)
        self.outbox = OutboxRepository(self._session)
        self.inbox = InboxRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc is not None:
            await self.rollback()
        await self._session_cm.__aexit__(exc_type, exc, tb)
        self._session_cm = self._session = None

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[Self, None]:
        if self._session is not None:
            async with self._session.begin():
                yield self

    async def commit(self):
        if self._session is not None:
            await self._session.commit()

    async def rollback(self):
        if self._session is not None:
            await self._session.rollback()
