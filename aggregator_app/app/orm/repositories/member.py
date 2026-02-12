"""Репозиторий участника события."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete

from app.orm.models import Member
from app.orm.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    """Репозиторий участника события."""

    async def create(self, json_data: dict[str, Any]) -> Member:
        """Создать участника."""
        member = Member(**json_data)
        self._session.add(member)
        return member

    async def get_by_id(self, ticket_id: UUID) -> Member | None:
        """Получить участника по ID."""
        return await self._session.get(Member, ticket_id)

    async def delete(self, ticket_id: UUID) -> bool:
        """Удалить участника."""
        stmt = delete(Member).where(Member.ticket_id == ticket_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)
