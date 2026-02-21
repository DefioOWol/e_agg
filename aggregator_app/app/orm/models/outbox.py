"""Модель очереди событий."""

import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.models.base import Base


class OutboxStatus(PyEnum):
    """Статус отправки."""

    WAITING = "waiting"
    SENT = "sent"


class Outbox(Base):
    """Модель очереди событий.

    Таблица: outbox.

    Атрибуты:
    - `id` - идентификатор; первичный ключ.
    - `payload` - JSON-данные; не может быть пустым.
    - `status`: `OutboxStatus` - статус отправки; не может быть пустым;
        по умолчанию 'waiting'.
    - `created_at`: datetime - время создания; не может быть пустым;
        по умолчанию 'NOW()'.

    """

    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus),
        nullable=False,
        index=True,
        default=OutboxStatus.WAITING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
