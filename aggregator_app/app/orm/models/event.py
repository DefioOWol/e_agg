"""Модель события."""

import uuid as uuid_pkg
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import UUID, DateTime, Enum, ForeignKey, String, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm.models.base import Base
from app.orm.models.member import Member
from app.orm.models.place import Place


class EventStatus(PyEnum):
    """Статус события."""

    NEW = "new"
    PUBLISHED = "published"


class Event(Base):
    """Модель события."""

    __tablename__ = "events"

    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    place_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("places.id"), nullable=False
    )
    place: Mapped[Place] = relationship(lazy="joined")
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
    members = relationship("Member", back_populates="event")

    @hybrid_property
    def number_of_visitors(self):
        return len(self.members)

    @number_of_visitors.expression
    def number_of_visitors(self):
        return (
            select(func.count(Member.ticker_id))
            .where(Member.event_id == self.id)
            .label("number_of_visitors")
        )
