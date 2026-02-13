"""Вспомогательные функции для репозиториев."""

from datetime import UTC, datetime
from uuid import uuid4

from app.orm.models import Base, Event, EventStatus, Place


def get_datetime_now():
    return datetime.now(UTC)


def create_place():
    place = Place(
        id=uuid4(),
        name="Test place",
        city="Test city",
        address="Test address",
        seats_pattern="A1-1000,B1-250",
        changed_at=get_datetime_now(),
        created_at=get_datetime_now(),
    )
    return place


def create_event(place: Place):
    event = Event(
        id=uuid4(),
        name="Test Event",
        place_id=place.id,
        event_time=get_datetime_now(),
        registration_deadline=get_datetime_now(),
        status=EventStatus.NEW,
        changed_at=get_datetime_now(),
        created_at=get_datetime_now(),
        status_changed_at=get_datetime_now(),
    )
    return event


def model_to_dict(model: Base):
    return {c.key: getattr(model, c.key) for c in model.__table__.c}
