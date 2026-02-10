"""Модель метаданных синхронизации."""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, Integer
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
    __table_args__ = (CheckConstraint("id = 1", name="ck_sync_meta_singleton"),)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1,
        autoincrement=False,
        nullable=False,
    )
    last_sync_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_changed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    sync_status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus), default=SyncStatus.NEVER, nullable=False
    )
