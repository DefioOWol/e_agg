"""Модель метаданных синхронизации."""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Date, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.models.base import Base


class SyncStatus(PyEnum):
    """Статус синхронизации."""

    NEVER = "never"
    PENDING = "pending"
    SYNCED = "synced"


class SyncMeta(Base):
    """Модель метаданных синхронизации."""

    __tablename__ = "sync_meta"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    last_sync_time: Mapped[datetime] = mapped_column(DateTime, default=None)
    last_changed_at: Mapped[date] = mapped_column(Date, default=None)
    sync_status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus), default=SyncStatus.NEVER, nullable=False
    )
