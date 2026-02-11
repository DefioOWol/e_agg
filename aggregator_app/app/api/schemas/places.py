"""Схемы мест проведения."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    """Базовая схема возвращаемого места проведения."""

    id: UUID
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class PlaceOutExtended(PlaceOut):
    """Расширенная схема возвращаемого места проведения."""

    seats_pattern: str
