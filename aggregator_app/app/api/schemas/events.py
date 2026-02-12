"""Схемы событий."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.api.schemas.places import PlaceOut, PlaceOutExtended
from app.orm.models.event import EventStatus


class EventOut(BaseModel):
    """Базовая схема возвращаемого события.

    Атрибуты:
    - `id` - UUID события.
    - `name` - Название события.
    - `place`: `PlaceOut` - Место проведения события.
    - `event_time`: datetime - Время начала события.
    - `registration_deadline`: datetime - Время окончания регистрации.
    - `status`: `EventStatus` - Статус события.
    - `number_of_visitors` - Количество участников.

    """

    id: UUID
    name: str
    place: PlaceOut
    event_time: datetime
    registration_deadline: datetime
    status: EventStatus
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class EventOutExtendedPlace(EventOut):
    """Схема возвращаемого события с расширенным местом проведения.

    Наследуется от `EventOut`.

    Атрибуты:
    - `place`: `PlaceOutExtended` - Место проведения события.

    """

    place: PlaceOutExtended


class EventListOutPaginated(BaseModel):
    """Пагинированный список событий.

    Атрибуты:
    - `count` - Общее количество событий.
    - `next` - URL следующей страницы.
    - `previous` - URL предыдущей страницы.
    - `results`: list[`EventOut`] - Список событий.

    """

    count: int
    next: HttpUrl | None
    previous: HttpUrl | None
    results: list[EventOut]
