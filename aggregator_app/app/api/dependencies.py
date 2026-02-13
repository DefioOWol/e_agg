"""Зависимости API."""

from typing import Annotated

from fastapi import Depends

from app.orm.db_manager import db_manager
from app.orm.uow import IUnitOfWork, SqlAlchemyUnitOfWork
from app.services.events import EventsService
from app.services.events_provider import (
    EventsProviderClient,
    IEventsProviderClient,
)
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
