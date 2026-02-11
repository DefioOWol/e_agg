"""API регистрации участников."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas.members import MemberIn
from app.orm.models import EventStatus
from app.services import EventsService, TicketsService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def register(
    member: MemberIn,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Зарегистрировать участника на событие."""
    event = await EventsService(session).get_by_id(member.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not published",
        )
    if datetime.now(UTC) > event.registration_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The registration time has expired",
        )
    seats = await EventsService(session).get_seats(member.event_id)
    if member.seat not in seats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat is not available",
        )
    ticket_id = await TicketsService(session).register(
        member.event_id, member.model_dump()
    )
    return {"ticket_id": ticket_id}
