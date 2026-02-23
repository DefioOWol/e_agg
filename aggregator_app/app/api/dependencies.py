"""Зависимости API."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status

from app.orm.db_manager import db_manager
from app.orm.uow import IUnitOfWork, SqlAlchemyUnitOfWork
from app.services.events import EventsService
from app.services.events_provider import (
    EventsProviderClient,
    IEventsProviderClient,
)
from app.services.inbox import InboxService, get_inbox_service
from app.services.tickets import TicketsService


def get_uow() -> IUnitOfWork:
    return SqlAlchemyUnitOfWork(db_manager)


def get_events_provider_client() -> IEventsProviderClient:
    return EventsProviderClient()


def get_events_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    client: Annotated[
        IEventsProviderClient, Depends(get_events_provider_client)
    ],
) -> EventsService:
    return EventsService(uow, client)


def get_tickets_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    client: Annotated[
        IEventsProviderClient, Depends(get_events_provider_client)
    ],
) -> TicketsService:
    return TicketsService(uow, client)


async def get_idempotency_data(
    request: Request,
    inbox_service: Annotated[InboxService, Depends(get_inbox_service)],
) -> dict[str, Any] | None:
    body = await request.json()
    if not (idempotency_key := body.get("idempotency_key")):
        return None

    body.pop("idempotency_key")
    inbox = await inbox_service.get_inbox(idempotency_key)
    hashed, has_conflict = inbox_service.check_conflict(
        inbox and inbox.request_hash, body
    )

    if inbox is None:
        return {
            "key": idempotency_key,
            "request_hash": hashed,
        }

    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key already exists",
        )

    return {"response": inbox.response}
