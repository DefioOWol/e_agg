"""Модуль взаимодействия с EventsProviderAPI."""

from datetime import date
from typing import Any

import backoff
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientResponseError

from app.config import settings


class EventsProviderClient:
    """Клиент для взаимодействия с EventsProviderAPI."""

    BASE_URL = "http://events-provider.dev-1.python-labs.ru"

    def __init__(self, total_timeout: int = 30, connect_timeout: int = 10):
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
        (ClientTimeout, ClientResponseError),
        max_tries=3,
        giveup=lambda e: (
            isinstance(e, ClientResponseError)
            and e.status not in {429, 500, 502, 503, 504}
        ),
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
