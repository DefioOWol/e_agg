"""Утилиты и вспомогательные элементы сервисов."""

import logging
from datetime import UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, filename="app.log", filemode="w")

scheduler = AsyncIOScheduler(timezone=UTC)
