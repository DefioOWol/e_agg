"""Утилиты и вспомогательные элементы сервисов."""

from datetime import UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone=UTC)
