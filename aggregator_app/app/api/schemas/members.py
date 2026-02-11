"""Схемы регистрации участников."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemberIn(BaseModel):
    """Схема регистрации участника."""

    event_id: UUID
    first_name: str = Field(min_length=2, max_length=32)
    last_name: str = Field(min_length=2, max_length=32)
    email: EmailStr
    seat: str = Field(pattern=r"^[A-Z][0-9]+$")
