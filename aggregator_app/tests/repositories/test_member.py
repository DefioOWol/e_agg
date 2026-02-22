"""Тесты репозитория участников."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.models import Event
from app.orm.repositories.member import IMemberRepository, MemberRepository


def _get_member_repository(session: AsyncSession) -> IMemberRepository:
    return MemberRepository(session)


def _create_member(repo: IMemberRepository, ticket_id: UUID, event: Event):
    return repo.create(
        {
            "ticket_id": ticket_id,
            "first_name": "Иван",
            "last_name": "Иванов",
            "seat": "A1",
            "email": "ivan@example.com",
            "event_id": event.id,
        }
    )


@pytest.mark.asyncio
async def test_create_and_get_by_id(session: AsyncSession, event: Event):
    repo = _get_member_repository(session)
    ticket_id = uuid4()
    _create_member(repo, ticket_id, event)
    await session.flush()

    member = await repo.get_by_id(ticket_id, load_event=False)
    assert member is not None
    assert member.ticket_id == ticket_id
    assert member.event_id == event.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(session: AsyncSession):
    repo = _get_member_repository(session)
    member = await repo.get_by_id(uuid4(), load_event=False)
    assert member is None


@pytest.mark.asyncio
async def test_get_by_id_with_load_event(session: AsyncSession, event: Event):
    repo = _get_member_repository(session)
    ticket_id = uuid4()
    _create_member(repo, ticket_id, event)
    await session.flush()

    member = await repo.get_by_id(ticket_id, load_event=True)
    assert member is not None
    assert member.event is not None
    assert member.event.id == event.id


@pytest.mark.asyncio
async def test_delete(session: AsyncSession, event: Event):
    repo = _get_member_repository(session)
    ticket_id = uuid4()
    _create_member(repo, ticket_id, event)
    await session.flush()

    deleted = await repo.delete(ticket_id)
    assert deleted is True
    await session.flush()

    member = await repo.get_by_id(ticket_id, load_event=False)
    assert member is None
