"""Вспомогательные функции для тестов."""

from alembic.config import Config

from app.config import settings


def get_alembic_cfg() -> Config:
    """Получить конфигурацию Alembic."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config
