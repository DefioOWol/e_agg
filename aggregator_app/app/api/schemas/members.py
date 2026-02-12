"""Схемы регистрации участников."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemberIn(BaseModel):
    """Схема регистрации участника."""

    event_id: UUID
    first_name: str = Field(
        min_length=2, max_length=32, pattern=r"^[А-Я][а-я]+$"
    )
    last_name: str = Field(
        min_length=2, max_length=32, pattern=r"^[А-Я][а-я]+$"
    )
    email: EmailStr
    seat: str = Field(pattern=r"^[A-Z][1-9][0-9]{0,6}$")
