"""Модуль менеджера сессий базы данных."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings


class DBManager:
    """Менеджер сессий базы данных.

    Перед началом работы необходимо вызвать метод `init()`,
    после завершения - `close()`.

    """

    def __init__(self):
        """Инициализировать менеджер сессий базы данных."""
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    async def init(self):
        """Инициализировать соединение с базой данных."""
        self._engine = create_async_engine(
            settings.database_url, poolclass=NullPool
        )
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def close(self):
        """Закрыть соединение с базой данных."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получить генератор сессии базы данных.

        Является асинхронным контекстным менеджером.
        Возвращает объект сессии.
        При возникновении ошибки, сессия будет откатана.

        Исключения:
        - `ValueError` - если менеджер не инициализирован.

        """
        if self._sessionmaker is None:
            raise ValueError("DBManager is not initialized")
        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


db_manager = DBManager()
