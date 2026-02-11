"""Схемы событий."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.api.schemas.places import PlaceOut, PlaceOutExtended
from app.orm.models.event import EventStatus


class EventOut(BaseModel):
    """Базовая схема возвращаемого события."""

    id: UUID
    name: str
    place: PlaceOut
    event_time: datetime
    registration_deadline: datetime
    status: EventStatus
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class EventListOutPaginated(BaseModel):
    """Пагинированный список событий."""

    count: int
    next: HttpUrl | None
    previous: HttpUrl | None
    results: list[EventOut]


class EventOutExtendedPlace(EventOut):
    """Cхема возвращаемого события с расширенным местом проведения."""

    place: PlaceOutExtended
