"""API регистрации участников."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

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
    if datetime.now(UTC) >= event.registration_deadline:
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
    member_data = member.model_dump()
    ticket_id = await TicketsService(session).register(
        member_data.pop("event_id"), member_data
    )
    return {"ticket_id": ticket_id}


@router.delete("/{ticket_id}")
async def unregister(
    ticket_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Отменить регистрацию участника на событие."""
    ticket_service = TicketsService(session)
    member = await ticket_service.get_by_id(ticket_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    await ticket_service.unregister(member.event_id, ticket_id)
    return {"success": True}
