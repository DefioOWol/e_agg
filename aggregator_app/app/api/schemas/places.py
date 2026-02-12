"""Схемы мест проведения."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    """Базовая схема возвращаемого места проведения.

    Атрибуты:
    - `id` - UUID места проведения.
    - `name` - Название места проведения.
    - `city` - Город места проведения.
    - `address` - Адрес места проведения.

    """

    id: UUID
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class PlaceOutExtended(PlaceOut):
    """Расширенная схема возвращаемого места проведения.

    Наследуется от `PlaceOut`.

    Атрибуты:
    - `seats_pattern` - Формат посадочных мест.

    """

    seats_pattern: str
