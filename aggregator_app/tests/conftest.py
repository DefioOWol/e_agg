"""Конфигурация тестов."""

import pytest_asyncio

from app.orm.db_manager import db_manager


@pytest_asyncio.fixture(scope="session", autouse=True)
async def session_manager():
    """Инициализировать и закрыть менеджер сессии базы данных."""
    await db_manager.init()
    yield
    await db_manager.close()
