"""API событий."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi_filter import FilterDepends
from fastapi_simple_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import EventFilter, get_session
from app.api.schemas.events import EventListOutPaginated, EventOutExtendedPlace
from app.orm.models import EventStatus
from app.services.events import EventsService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListOutPaginated)
async def get_events(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    filter_: Annotated[EventFilter, FilterDepends(EventFilter)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int | None, Query(ge=1)] = None,
):
    """Получить пагинированный список событий."""
    events, count = await EventsService(session).get_paginated(
        filter_, page, page_size
    )

    next_url = None
    previous_url = None
    if page_size:
        if page * page_size < count:
            next_url = str(request.url.include_query_params(page=page + 1))
        if page > 1:
            previous_url = str(request.url.include_query_params(page=page - 1))

    return EventListOutPaginated(
        count=count,
        next=next_url,
        previous=previous_url,
        results=events,
    )


@router.get("/{event_id}", response_model=EventOutExtendedPlace)
async def get_event(
    event_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Получить событие по ID."""
    event = await EventsService(session).get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.get("/{event_id}/seats")
@cache(expire=30)
async def get_event_seats(
    request: Request,
    event_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Получить свободные места на событии."""
    event = await EventsService(session).get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not published",
        )
    seats = await EventsService(session).get_seats(event_id)
    return seats
