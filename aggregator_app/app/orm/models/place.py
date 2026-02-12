"""Модель места проведения события."""

import uuid as uuid_pkg
from datetime import datetime

from sqlalchemy import UUID, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.models.base import Base


class Place(Base):
    """Модель места проведения.

    Таблица: places.

    Атрибуты:
    - `id` - UUID места проведения; первичный ключ.
    - `name` - Название места проведения; не может быть пустым.
    - `city` - Город места проведения; не может быть пустым.
    - `address` - Адрес места проведения; не может быть пустым.
    - `seats_pattern` - Формат посадочных мест; не может быть пустым.
    - `changed_at`: datetime - время последнего изменения;
        не может быть пустым.
    - `created_at`: datetime - время создания; не может быть пустым.

    """

    __tablename__ = "places"

    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str] = mapped_column(String(128), nullable=False)
    seats_pattern: Mapped[str] = mapped_column(String(128), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
