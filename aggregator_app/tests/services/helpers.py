"""Вспомогательные функции для тестов сервисов."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from app.orm.models import EventStatus


def get_raw_iso_datetime_now() -> str:
    """Получить текущую дату и время в ISO формате."""
    return datetime.now(UTC).isoformat()


def get_raw_place() -> dict[str, Any]:
    """Получить словарь тестового места проведения."""
    return {
        "id": str(uuid4()),
        "name": "Test hall",
        "city": "Test city",
        "address": "Test street 1",
        "seats_pattern": "A1-A10",
        "changed_at": get_raw_iso_datetime_now(),
        "created_at": get_raw_iso_datetime_now(),
    }


def get_raw_event(status: EventStatus = EventStatus.NEW) -> dict[str, Any]:
    """Получить словарь тестового события."""
    return {
        "id": str(uuid4()),
        "name": "Test event",
        "place": get_raw_place(),
        "status": status.value,
        "event_time": get_raw_iso_datetime_now(),
        "registration_deadline": get_raw_iso_datetime_now(),
        "changed_at": get_raw_iso_datetime_now(),
        "created_at": get_raw_iso_datetime_now(),
        "status_changed_at": get_raw_iso_datetime_now(),
        "number_of_visitors": 10,
    }


def get_raw_member() -> dict[str, Any]:
    """Получить словарь тестового участника."""
    return {
        "first_name": "First",
        "last_name": "Last",
        "email": "first.last@example.com",
        "seat": "A1",
    }


class FakeEventsProviderClient:
    """Тестовый клиент EventsProviderAPI."""

    def __init__(self, **kwargs: Any):
        """Инициализировать клиент."""
        self._kwargs = kwargs

    async def get_events(
        self, changed_at: date, cursor: str | None = None
    ) -> dict[str, Any]:
        """Получить события из `pages` по ключу `cursor`."""
        return self._kwargs["pages"][cursor]

    @staticmethod
    def extract_cursor(response: dict[str, Any]) -> str | None:
        """Извлечь курсор из ответа по ключу `next`."""
        return response["next"]
