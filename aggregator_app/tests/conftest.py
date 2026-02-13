"""Конфигурация тестов."""

import pytest
import pytest_asyncio
from cashews import cache

from app.orm.db_manager import db_manager


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db_manager():
    await db_manager.init()
    yield
    await db_manager.close()


@pytest.fixture(scope="session", autouse=True)
def init_cache():
    cache.setup("mem://")
