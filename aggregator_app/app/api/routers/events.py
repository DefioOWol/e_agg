"""API событий."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi_filter import FilterDepends

from app.api.dependencies import get_events_service
from app.api.filters import EventFilter
from app.api.schemas.events import EventListOutPaginated, EventOutExtendedPlace
from app.orm.models import EventStatus
from app.services import EventsService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListOutPaginated)
async def get_events(
    request: Request,
    events_service: Annotated[EventsService, Depends(get_events_service)],
    filter_: Annotated[EventFilter, FilterDepends(EventFilter)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int | None, Query(ge=1)] = None,
):
    """Получить пагинированный список событий.

    Параметры запроса:
    - Параметры фильтрации из `EventFilter`.
    - `page` - Номер страницы; по умолчанию 1.
    - `page_size` - Размер страницы; по умолчанию None.

    Возвращает:
    - `EventListOutPaginated` - Пагинированный список событий.

    """
    events, count = await events_service.get_paginated(filter_, page, page_size)

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


@router.get(
    "/{event_id}",
    response_model=EventOutExtendedPlace,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Событие не найдено"},
    },
)
async def get_event(
    event_id: UUID,
    events_service: Annotated[EventsService, Depends(get_events_service)],
):
    """Получить событие по ID.

    Параметры пути:
    - `event_id` - UUID события.

    Возвращает:
    - `EventOutExtendedPlace` - Событие с расширенным местом проведения.

    """
    event = await events_service.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.get(
    "/{event_id}/seats",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Ошибка на внешнем API"
        },
        status.HTTP_404_NOT_FOUND: {"description": "Событие не найдено"},
        status.HTTP_400_BAD_REQUEST: {"description": "Событие не опубликовано"},
    },
)
async def get_event_seats(
    request: Request,
    event_id: UUID,
    events_service: Annotated[EventsService, Depends(get_events_service)],
):
    """Получить свободные места на событии.

    Параметры пути:
    - `event_id` - UUID события.

    Возвращает:
    - {"event_id": UUID, "available_seats": list[str]} - Свободные места.

    """
    event = await events_service.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not published",
        )
    seats = await events_service.get_seats(event_id)
    return {"event_id": event_id, "available_seats": seats}
