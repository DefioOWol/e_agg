"""API событий."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import EventFilter, get_session
from app.api.schemas.events import EventListOutPaginated
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
