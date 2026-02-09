"""Базовый репозиторий."""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Базовый репозиторий."""

    def __init__(self, session: AsyncSession):
        """Инициализировать репозиторий."""
        self._session = session
