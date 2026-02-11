"""Схемы мест проведения."""

from uuid import UUID

from pydantic import BaseModel


class PlaceOut(BaseModel):
    """Базовая схема возвращаемого места проведения."""

    id: UUID
    name: str
    city: str
    address: str


class PlaceOutExtended(PlaceOut):
    """Расширенная схема возвращаемого места проведения."""

    seats_pattern: str
