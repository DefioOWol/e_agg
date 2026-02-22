"""Модель события."""

import uuid as uuid_pkg
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import UUID, DateTime, Enum, ForeignKey, String, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.orm.models.base import Base
from app.orm.models.member import Member


class EventStatus(PyEnum):
    """Статус события."""

    NEW = "new"
    PUBLISHED = "published"
    OTHER = "other"


class Event(Base):
    """Модель события.

    Таблица: events.

    Атрибуты:
    - `id` - UUID события; первичный ключ.
    - `name` - название события; не может быть пустой.
    - `place_id` - UUID места проведения; внешний ключ к таблице places.
    - `place`: `Place` - связанное место проведения.
    - `event_time`: datetime - время проведения события; не может быть пустым.
    - `registration_deadline`: datetime - время окончания регистрации;
        не может быть пустым.
    - `status`: `EventStatus` - статус события; не может быть пустым.
    - `changed_at`: datetime - время последнего изменения;
        не может быть пустым.
    - `created_at`: datetime - время создания; не может быть пустым.
    - `status_changed_at`: datetime - время последнего изменения статуса;
        не может быть пустым.

    Свойства:
    - `number_of_visitors` - количество зарегистрированных участников `Member`.

    """

    __tablename__ = "events"

    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    place_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("places.id"), nullable=False
    )
    place = relationship("Place", lazy="joined")
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    number_of_visitors = column_property(
        select(func.count(Member.ticket_id))
        .where(Member.event_id == id)
        .correlate_except(Member)
        .scalar_subquery()
    )
