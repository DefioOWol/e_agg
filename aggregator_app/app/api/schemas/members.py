"""Схемы регистрации участников."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemberIn(BaseModel):
    """Схема регистрации участника.

    Атрибуты:
    - `event_id` - UUID события для регистрации.
    - `first_name` - Имя участника.
    - `last_name` - Фамилия участника.
    - `email` - Email участника.
    - `seat` - Желаемое место.

    """

    event_id: UUID
    first_name: str = Field(
        min_length=2, max_length=32, pattern=r"^[A-ZА-Я][a-zа-я]+$"
    )
    last_name: str = Field(
        min_length=2, max_length=32, pattern=r"^[A-ZА-Я][a-zа-я]+$"
    )
    email: EmailStr
    seat: str = Field(pattern=r"^[A-Z][1-9][0-9]{0,6}$")
