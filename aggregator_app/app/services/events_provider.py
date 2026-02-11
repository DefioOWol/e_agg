"""Модуль взаимодействия с EventsProviderAPI."""

from datetime import UTC, date, datetime
from typing import Any

import backoff
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from sqlalchemy import DateTime

from app.config import settings
from app.orm.models import Base, Event, EventStatus, Place


class EventsProviderClient:
    """Клиент для взаимодействия с EventsProviderAPI."""

    BASE_URL = "http://events-provider.dev-1.python-labs.ru"

    def __init__(self, total_timeout: int = 10, connect_timeout: int = 5):
        """Инициализировать клиент."""
        timeout = ClientTimeout(total=total_timeout, connect=connect_timeout)
        self._session = ClientSession(
            self.BASE_URL,
            headers={"x-api-key": settings.lms_api_key.get_secret_value()},
            timeout=timeout,
            raise_for_status=True,
        )

    @backoff.on_exception(
        backoff.expo,
        (TimeoutError, ClientConnectionError, ClientResponseError),
        max_tries=3,
    )
    async def get_events(
        self, changed_at: date, cursor: str | None = None
    ) -> dict[str, Any]:
        """Получить события."""
        url = f"/api/events/?changed_at={changed_at.isoformat()}"
        if cursor:
            url += f"&cursor={cursor}"
        async with self._session.get(url) as response:
            return await response.json()

    async def close(self):
        """Закрыть сессию."""
        await self._session.close()

    async def __aenter__(self):
        """Вход в контекстный менеджер."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Выход из контекстного менеджера."""
        await self.close()

    @staticmethod
    def extract_cursor(response: dict[str, Any]) -> str | None:
        """Извлечь курсор из ответа."""
        if (cursor := response.get("next")) is not None:
            cursor = cursor.rsplit("cursor=", 1)[1]
        return cursor


class EventsPaginator:
    """Пагинатор событий EventsProviderAPI."""

    def __init__(self, client: EventsProviderClient, changed_at: date):
        """Инициализировать пагинатор."""
        self._client = client
        self._changed_at = changed_at
        self._cursor = None
        self._events = []
        self._current = 0

    def __aiter__(self):
        """Получить итератор событий."""
        return self

    async def __anext__(self) -> dict[str, Any]:
        """Получить следующее событие."""
        end_status = self._current >= len(self._events)
        if self._cursor is None and end_status and self._current:
            raise StopAsyncIteration
        if end_status:
            response = await self._client.get_events(
                self._changed_at, self._cursor
            )
            self._cursor = self._client.extract_cursor(response)
            self._events = response["results"]
            self._current = 0
        event = self._events[self._current]
        self._current += 1
        return event


class EventsProviderParser:
    """Парсер данных EventsProviderAPI."""

    def parse_event_dict(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Разобрать событие и вернуть словари с данными."""
        place_data = data.pop("place")
        self._prepare_place(place_data)
        self._prepare_event(data)
        return data | {"place_id": place_data["id"]}, place_data

    def _prepare_event(self, event_data: dict[str, Any]):
        """Подготовить данные события."""
        del event_data["number_of_visitors"]
        event_data["status"] = EventStatus(event_data["status"])
        self._convert_datetime(event_data, Event)

    def _prepare_place(self, place_data: dict[str, Any]):
        """Подготовить данные места проведения."""
        self._convert_datetime(place_data, Place)

    def _convert_datetime(self, data: dict[str, Any], cls_: type[Base]):
        """Конвертировать даты."""
        for c in cls_.__table__.c:
            if isinstance(c.type, DateTime) and c.key in data:
                data[c.key] = datetime.fromisoformat(data[c.key]).astimezone(
                    UTC
                )
