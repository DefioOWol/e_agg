"""Репозиторий участника события."""

from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from app.orm.models import Member
from app.orm.repositories.base import BaseRepository


class IMemberRepository(Protocol):
    """Интерфейс репозитория участника."""

    async def create(self, json_data: dict[str, Any]) -> Member:
        """Создать участника.

        Данные словаря должны соответствовать полям модели `Member`
        и требуемым типам данных.

        """

    async def get_by_id(
        self, ticket_id: UUID, *, load_event: bool
    ) -> Member | None:
        """Получить участника по ID билета.

        Аргументы:
        - `ticket_id` - UUID билета.
        - `load_event` - Флаг подгрузки связанного события.

        Возвращает:
        - Участник или None, если не найден.

        """

    async def delete(self, ticket_id: UUID) -> bool:
        """Удалить участника по ID билета."""


class MemberRepository(BaseRepository, IMemberRepository):
    """Репозиторий участника события.

    Реализует `IMemberRepository`.

    """

    async def create(self, json_data: dict[str, Any]) -> Member:
        member = Member(**json_data)
        self._session.add(member)
        return member

    async def get_by_id(
        self, ticket_id: UUID, *, load_event: bool
    ) -> Member | None:
        stmt = select(Member)
        if load_event:
            stmt = stmt.options(joinedload(Member.event))
        stmt = stmt.where(Member.ticket_id == ticket_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, ticket_id: UUID) -> bool:
        stmt = delete(Member).where(Member.ticket_id == ticket_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)
