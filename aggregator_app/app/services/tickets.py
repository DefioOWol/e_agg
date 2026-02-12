"""Сервис регистрации участников."""

from typing import Any
from uuid import UUID

from aiohttp import ClientResponseError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.repositories import MemberRepository
from app.services.events_provider import (
    EventsProviderClient,
    with_events_provider,
)


class TicketsService:
    """Сервис регистрации участников."""

    def __init__(self, session: AsyncSession):
        """Инициализировать сервис регистрации участников."""
        self._session = session
        self._member_repo = MemberRepository(session)

    async def register(
        self, event_id: UUID, member_data: dict[str, Any]
    ) -> str:
        """Зарегистрировать участника на событие."""
        await with_events_provider(
            self._register_member,
            func_kwargs={"event_id": event_id, "member_data": member_data},
            on_success=self._create_member,
            on_success_kwargs={
                "event_id": event_id,
                "member_data": member_data,
            },
            on_error=self._raise_external_register_error,
        )

    async def _register_member(
        self,
        client: EventsProviderClient,
        event_id: UUID,
        member_data: dict[str, Any],
    ) -> str:
        """Зарегистрировать участника на событие."""
        result = await client.register_member(event_id, member_data)
        return result["ticket_id"]

    async def _create_member(
        self, ticket_id: str, event_id: UUID, member_data: dict[str, Any]
    ) -> str:
        """Создать участника."""
        member_data.update({"event_id": event_id, "ticket_id": ticket_id})
        await self._member_repo.create(member_data)
        await self._session.commit()
        return ticket_id

    async def _raise_external_register_error(self, e: Exception):
        """Вызвать ошибку на внешнюю регистрацию."""
        if (
            isinstance(e, ClientResponseError)
            and e.status == status.HTTP_400_BAD_REQUEST
        ):
            raise HTTPException(status_code=e.status, detail=e.message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
