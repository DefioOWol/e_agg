"""Тесты репозитория событий."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.models import EventStatus
from app.orm.repositories.event import EventRepository, IEventRepository
from tests.repositories.helpers import create_event, create_place, model_to_dict


def _get_event_repository(session: AsyncSession) -> IEventRepository:
    return EventRepository(session)


@pytest.mark.asyncio
async def test_get_paginated_with_page_size(session: AsyncSession):
    place = create_place()
    session.add(place)
    await session.flush()

    for _ in range(5):
        session.add(create_event(place))
    await session.flush()

    repo = _get_event_repository(session)
    result = await repo.get_paginated(page=1, page_size=2)
    assert len(result) == 2

    result = await repo.get_paginated(page=2, page_size=2)
    assert len(result) == 2

    result = await repo.get_paginated(page=3, page_size=2)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_paginated_without_page_size(session: AsyncSession):
    place = create_place()
    session.add(place)
    await session.flush()

    for _ in range(3):
        session.add(create_event(place))
    await session.flush()

    repo = _get_event_repository(session)
    result = await repo.get_paginated(page=1, page_size=None)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_upsert_create_new(session: AsyncSession):
    repo = _get_event_repository(session)
    place = create_place()
    session.add(place)
    await session.flush()

    event = create_event(place)
    await repo.upsert([model_to_dict(event)])
    await session.flush()

    event_got = await repo.get_by_id(event.id)
    assert event_got is not None
    assert event_got.id == event.id


@pytest.mark.asyncio
async def test_upsert_update_existing(session: AsyncSession):
    repo = _get_event_repository(session)
    place = create_place()
    session.add(place)
    await session.flush()

    event = create_event(place)
    session.add(event)
    await session.flush()

    data = model_to_dict(event)
    data["name"] = "Updated event name"
    data["status"] = EventStatus.PUBLISHED

    await repo.upsert([data])
    await session.flush()
    await session.refresh(event)

    assert event.name == "Updated event name"
    assert event.status == EventStatus.PUBLISHED
