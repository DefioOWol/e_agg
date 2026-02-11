"""Репозиторий участника события."""

from typing import Any

from app.orm.models import Member
from app.orm.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    """Репозиторий участника события."""

    async def create(self, json_data: dict[str, Any]) -> Member:
        """Создать участника."""
        member = Member(**json_data)
        self._session.add(member)
        return member
