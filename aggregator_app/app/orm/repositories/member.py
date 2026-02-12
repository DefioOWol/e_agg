"""Репозиторий участника события."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from app.orm.models import Member
from app.orm.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    """Репозиторий участника события."""

    async def create(self, json_data: dict[str, Any]) -> Member:
        """Создать участника.

        Данные словаря должны соответствовать полям модели `Member`
        и требуемым типам данных.

        """
        member = Member(**json_data)
        self._session.add(member)
        return member

    async def get_by_id(
        self, ticket_id: UUID, *, load_event: bool
    ) -> Member | None:
        """Получить участника по ID билета.

        Аргументы:
        - `ticket_id` - UUID билета.
        - `load_event` - Флаг подгрузки связанного события.

        Возвращает:
        - `Member` | None - Участник или None, если не найден.

        """
        stmt = select(Member)
        if load_event:
            stmt = stmt.options(joinedload(Member.event))
        stmt = stmt.where(Member.ticket_id == ticket_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, ticket_id: UUID) -> bool:
        """Удалить участника по ID билета.

        Возвращает:
        - bool - статус удаления.

        """
        stmt = delete(Member).where(Member.ticket_id == ticket_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)
