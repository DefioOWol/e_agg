"""Базовый репозиторий."""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Базовый репозиторий."""

    def __init__(self, session: AsyncSession):
        """Инициализировать репозиторий с сессией базы данных."""
        self._session = session
