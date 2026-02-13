"""Тесты репозитория участников."""

from uuid import UUID, uuid4

import pytest

from app.orm.models import Event, Member
from app.orm.repositories import MemberRepository


async def _create_member(
    repo: MemberRepository, ticket_id: UUID, event: Event
) -> Member:
    """Создать участника."""
    return await repo.create(
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
async def test_create_and_get_by_id(session, event):
    """Проверить создание и получение участника."""
    repo = MemberRepository(session)
    ticket_id = uuid4()
    await _create_member(repo, ticket_id, event)
    await session.flush()

    member = await repo.get_by_id(ticket_id, load_event=False)
    assert member is not None
    assert member.ticket_id == ticket_id
    assert member.event_id == event.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(session):
    """Проверить получение несуществующего участника."""
    repo = MemberRepository(session)
    member = await repo.get_by_id(uuid4(), load_event=False)
    assert member is None


@pytest.mark.asyncio
async def test_get_by_id_load_event(session, event):
    """Проверить получение участника с подгрузкой события."""
    repo = MemberRepository(session)
    ticket_id = uuid4()
    await _create_member(repo, ticket_id, event)
    await session.flush()

    member = await repo.get_by_id(ticket_id, load_event=True)
    assert member is not None
    assert member.event is not None
    assert member.event.id == event.id


@pytest.mark.asyncio
async def test_delete(session, event):
    """Проверить удаление участника."""
    repo = MemberRepository(session)
    ticket_id = uuid4()
    await _create_member(repo, ticket_id, event)
    await session.flush()

    deleted = await repo.delete(ticket_id)
    assert deleted is True
    await session.flush()

    member = await repo.get_by_id(ticket_id, load_event=False)
    assert member is None
