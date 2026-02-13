"""Конфигурация тестов репозиториев."""

import pytest
import pytest_asyncio

from alembic import command
from app.orm.db_manager import db_manager
from tests.helpers import get_alembic_cfg
from tests.repositories.helpers import create_event, create_place


@pytest.fixture(scope="module", autouse=True)
def apply_migrations():
    """Применить миграции до модуля тестов и откатить после."""
    command.upgrade(get_alembic_cfg(), "head")
    yield
    command.downgrade(get_alembic_cfg(), "base")


@pytest_asyncio.fixture
async def session():
    async with db_manager.session() as session:
        yield session


@pytest_asyncio.fixture
async def event(session):
    place = create_place()
    event = create_event(place)
    session.add(place)
    await session.flush()
    session.add(event)
    await session.flush()
    yield event
