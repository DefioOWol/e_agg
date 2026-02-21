"""Сервис регистрации участников."""

from typing import Any
from uuid import UUID

from aiohttp import ClientResponseError
from fastapi import HTTPException, status

from app.orm.models import Member, OutboxType
from app.orm.uow import IUnitOfWork
from app.services.events_provider import IEventsProviderClient
from app.services.utils import with_external_client


class TicketsService:
    """Сервис регистрации участников."""

    def __init__(
        self,
        uow: IUnitOfWork,
        client: IEventsProviderClient,
    ):
        self._uow = uow
        self._client = client

    async def get_by_id(
        self, ticket_id: UUID, *, load_event: bool = False
    ) -> Member | None:
        """Получить участника по ID билета.

        Аргументы:
        - `ticket_id` - UUID билета участника.
        - `load_event` - Флаг подгрузки связанного события; по умолчанию False.

        """
        async with self._uow as uow:
            return await uow.members.get_by_id(
                ticket_id,
                load_event=load_event,
            )

    async def register(
        self, event_id: UUID, member_data: dict[str, Any]
    ) -> str:
        """Зарегистрировать участника на событие.

        Аргументы:
        - `event_id` - UUID события.
        - `member_data` - Данные участника, готовые к JSON-сериализации.

        Возвращает:
        - UUID билета участника.

        """
        return await with_external_client(
            self._client,
            self._register_member,
            func_kwargs={"event_id": event_id, "member_data": member_data},
            on_success=self._create_member,
            on_success_kwargs={
                "event_id": event_id,
                "member_data": member_data,
            },
            on_error=self._raise_external_error,
        )

    async def _register_member(
        self,
        client: IEventsProviderClient,
        event_id: UUID,
        member_data: dict[str, Any],
    ) -> str:
        """Зарегистрировать участника на событие."""
        result = await client.register_member(event_id, member_data)
        return result["ticket_id"]

    async def _create_member(
        self, ticket_id: str, event_id: UUID, member_data: dict[str, Any]
    ) -> str:
        """Создать участника в локальной базе данных."""
        member_data.update({"event_id": event_id, "ticket_id": ticket_id})
        async with self._uow as uow:
            async with uow.begin():
                await uow.members.create(member_data)
                await uow.outbox.create(
                    OutboxType.TICKET_REGISTER, member_data
                )
        return ticket_id

    async def unregister(self, event_id: UUID, ticket_id: UUID):
        """Отменить регистрацию участника на событие."""
        await with_external_client(
            self._client,
            self._unregister_member,
            func_kwargs={"event_id": event_id, "ticket_id": ticket_id},
            on_success=self._delete_member,
            on_success_kwargs={"ticket_id": ticket_id},
            on_error=self._raise_external_error,
        )

    async def _unregister_member(
        self, client: IEventsProviderClient, event_id: UUID, ticket_id: UUID
    ):
        """Отменить регистрацию участника на событие."""
        await client.unregister_member(event_id, ticket_id)

    async def _delete_member(self, _: None, ticket_id: UUID):
        """Удалить участника."""
        async with self._uow as uow:
            await uow.members.delete(ticket_id)
            await uow.commit()

    async def _raise_external_error(self, e: Exception):
        """Вызвать ошибку на внешнюю регистрацию.

        При ошибке типа `ClientResponseError` с кодом 400
        будет выброшена ошибка HTTP 400, в остальных случаях - HTTP 500.

        """
        if (
            isinstance(e, ClientResponseError)
            and e.status == status.HTTP_400_BAD_REQUEST
        ):
            raise HTTPException(status_code=e.status, detail=e.message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
