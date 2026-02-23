"""Модель идемпотентности."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.orm.models.base import Base


class Inbox(Base):
    """Модель идемпотентности.

    Таблица: inbox.

    Атрибуты:
    - `key` - ключ идемпотентности; первичный ключ.
    - `request_hash` - хэш запроса; не может быть пустым.
    - `response` - JSON-данные ответа; не может быть пустым.
    - `expires_at`: datetime - время истечения срока действия;
        не может быть пустым.

    """

    __tablename__ = "inbox"

    key: Mapped[str] = mapped_column(
        String(128), primary_key=True, nullable=False
    )
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response: Mapped[dict] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: (
            datetime.now(UTC) + timedelta(seconds=settings.inbox_seconds_ttl)
        ),
    )
