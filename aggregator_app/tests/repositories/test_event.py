"""Тесты репозитория событий."""

import pytest
from sqlalchemy import select

from app.orm.models import Event, EventStatus
from app.orm.repositories import EventRepository
from tests.repositories.helpers import create_event, create_place, model_to_dict


@pytest.mark.asyncio
async def test_get_paginated_with_page_size(session):
    """Проверить пагинацию с указанным размером страницы."""
    place = create_place()
    session.add(place)
    await session.flush()

    for _ in range(5):
        session.add(create_event(place))
    await session.flush()

    repo = EventRepository(session)
    stmt = select(Event)
    result = await repo.get_paginated(stmt, page=1, page_size=2)
    assert len(result) == 2

    result = await repo.get_paginated(stmt, page=2, page_size=2)
    assert len(result) == 2

    result = await repo.get_paginated(stmt, page=3, page_size=2)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_paginated_without_page_size(session):
    """Проверить, что при page_size=None пагинация не применяется."""
    place = create_place()
    session.add(place)
    await session.flush()

    for _ in range(3):
        session.add(create_event(place))
    await session.flush()

    repo = EventRepository(session)
    result = await repo.get_paginated(select(Event), page=1, page_size=None)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_upsert_create_new(session):
    """Проверить создание новой записи через upsert."""
    repo = EventRepository(session)
    place = create_place()
    session.add(place)
    await session.flush()

    event = create_event(place)
    await repo.upsert([model_to_dict(event)])
    await session.flush()

    stmt = select(Event).where(Event.id == event.id)
    event_got = await repo.get_select_scalar(stmt)
    assert event_got is not None
    assert event_got.id == event.id


@pytest.mark.asyncio
async def test_upsert_update_existing(session):
    """Проверить обновление существующей записи через upsert."""
    repo = EventRepository(session)
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
