"""Тесты миграций."""

import pytest
from alembic.script import Script, ScriptDirectory

from alembic import command
from tests.helpers import get_alembic_cfg


def get_revisions() -> list[Script]:
    """Получить список миграций."""
    revisions_dir = ScriptDirectory.from_config(get_alembic_cfg())
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()
    return revisions


@pytest.mark.parametrize("revision", get_revisions())
def test_migrations_stairway(revision: Script):
    """Тест пошаговой миграции."""
    alembic_cfg = get_alembic_cfg()
    command.upgrade(alembic_cfg, revision.revision)
    command.downgrade(alembic_cfg, revision.down_revision or "-1")
    command.upgrade(alembic_cfg, revision.revision)
