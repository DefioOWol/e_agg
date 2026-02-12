"""Модель участника события."""

import uuid as uuid_pkg

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm.models.base import Base


class Member(Base):
    """Модель участника.

    Таблица: members.

    Атрибуты:
    - `ticket_id` - UUID билета; первичный ключ.
    - `first_name` - Имя участника; не может быть пустым.
    - `last_name` - Фамилия участника; не может быть пустым.
    - `seat` - Место участника; не может быть пустым.
    - `email` - Email участника; не может быть пустым.
    - `event_id` - UUID события; внешний ключ к таблице events.
    - `event`: `Event` - связанное событие.

    """

    __tablename__ = "members"

    ticket_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    seat: Mapped[str] = mapped_column(String(16), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False)
    event_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False
    )
    event = relationship("Event")
