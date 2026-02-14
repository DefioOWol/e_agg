"""Тесты репозитория мест проведения."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.models import Place
from app.orm.repositories.place import IPlaceRepository, PlaceRepository
from tests.helpers import create_place, model_to_dict


def _get_place_repository(session: AsyncSession) -> IPlaceRepository:
    return PlaceRepository(session)


@pytest.mark.asyncio
async def test_upsert_create_new(session: AsyncSession):
    repo = _get_place_repository(session)
    place = create_place()

    await repo.upsert([model_to_dict(place)])
    await session.flush()

    place_got = await session.get(Place, place.id)
    assert place_got is not None
    assert place_got.id == place.id


@pytest.mark.asyncio
async def test_upsert_update_existing(session: AsyncSession):
    repo = _get_place_repository(session)
    place = create_place()
    session.add(place)
    await session.flush()

    data = model_to_dict(place)
    data["name"] = "Updated place name"

    await repo.upsert([data])
    await session.flush()
    await session.refresh(place)

    assert place.name == "Updated place name"
