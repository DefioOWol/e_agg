"""Конфигурация тестов миграций."""

import pytest

from alembic import command
from tests.helpers import get_alembic_cfg


@pytest.fixture(scope="module", autouse=True)
def downgrade_migrations():
    yield
    command.downgrade(get_alembic_cfg(), "base")
