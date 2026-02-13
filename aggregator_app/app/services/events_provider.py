"""Модуль взаимодействия с EventsProviderAPI."""

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from datetime import UTC, date, datetime
from typing import Any, Protocol
from uuid import UUID

import backoff
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from sqlalchemy import DateTime

from app.config import settings
from app.orm.models import Base, Event, EventStatus, Place


class IEventsProviderClient(
    AbstractAsyncContextManager["IEventsProviderClient"], Protocol
):
    """Интерфейс клиента для взаимодействия с EventsProviderAPI."""

    BASE_URL = "http://events-provider.dev-1.python-labs.ru"

    async def get_events(
        self, changed_at: date, cursor: str | None = None
    ) -> dict[str, Any]:
        """Получить события.

        Аргументы:
        - `changed_at` - Дата последнего изменения в ISO формате.
        - `cursor` - Курсор пагинации; по умолчанию None.

        """

    async def get_seats(self, event_id: UUID) -> dict[str, Any]:
        """Получить свободные места на событии."""

    async def register_member(
        self, event_id: UUID, member_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Зарегистрировать участника на событие.

        Аргументы:
        - `event_id` - UUID события.
        - `member_data` - Данные участника.

        """

    async def unregister_member(
        self, event_id: UUID, ticket_id: UUID
    ) -> dict[str, Any]:
        """Отменить регистрацию участника на событие."""

    @staticmethod
    def extract_cursor(response: dict[str, Any]) -> str | None:
        """Извлечь курсор из ответа."""
        if (cursor := response.get("next")) is not None:
            cursor = cursor.rsplit("cursor=", 1)[1]
        return cursor


class EventsProviderClient(IEventsProviderClient):
    """Клиент для взаимодействия с EventsProviderAPI.

    Реализует `IEventsProviderClient`.

    """

    _BACKOFF_ON_EXCEPTION = backoff.on_exception(
        backoff.expo,
        (TimeoutError, ClientConnectionError, ClientResponseError),
        max_tries=3,
    )

    def __init__(self, total_timeout: int = 10, connect_timeout: int = 5):
        """Инициализировать клиент.

        Аргументы:
        - `total_timeout` - Максимальное время ожидания всего запроса;
            по умолчанию 10 секунд.
        - `connect_timeout` - Максимальное время ожидания соединения;
            по умолчанию 5 секунд.

        """
        self._timeout = ClientTimeout(
            total=total_timeout, connect=connect_timeout
        )
        self._session: ClientSession | None = None

    @_BACKOFF_ON_EXCEPTION
    async def get_events(
        self, changed_at: date, cursor: str | None = None
    ) -> dict[str, Any]:
        """Получить события.

        Аргументы:
        - `changed_at` - Дата последнего изменения в ISO формате.
        - `cursor` - Курсор пагинации; по умолчанию None.

        """
        url = f"/api/events/?changed_at={changed_at.isoformat()}"
        if cursor:
            url += f"&cursor={cursor}"
        async with self._session.get(url) as response:
            return await response.json()

    @_BACKOFF_ON_EXCEPTION
    async def get_seats(self, event_id: UUID) -> dict[str, Any]:
        """Получить свободные места на событии."""
        url = f"/api/events/{event_id}/seats/"
        async with self._session.get(url) as response:
            return await response.json()

    @_BACKOFF_ON_EXCEPTION
    async def register_member(
        self, event_id: UUID, member_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Зарегистрировать участника на событие.

        Аргументы:
        - `event_id` - UUID события.
        - `member_data` - Данные участника.

        """
        url = f"/api/events/{event_id}/register/"
        async with self._session.post(url, json=member_data) as response:
            return await response.json()

    @_BACKOFF_ON_EXCEPTION
    async def unregister_member(
        self, event_id: UUID, ticket_id: UUID
    ) -> dict[str, Any]:
        """Отменить регистрацию участника на событие."""
        url = f"/api/events/{event_id}/unregister/"
        async with self._session.delete(
            url, json={"ticket_id": str(ticket_id)}
        ) as response:
            return await response.json()

    async def __aenter__(self):
        self._session = ClientSession(
            self.BASE_URL,
            headers={"x-api-key": settings.lms_api_key.get_secret_value()},
            timeout=self._timeout,
            raise_for_status=True,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._session.close()
        self._session = None


async def with_events_provider(
    client: IEventsProviderClient,
    func: Callable[..., Awaitable[Any]],
    *,
    func_kwargs: dict[str, Any] | None = None,
    on_success: Callable[..., Awaitable[Any]] | None = None,
    on_success_kwargs: dict[str, Any] | None = None,
    on_error: Callable[..., Awaitable[Any]] | None = None,
    on_error_kwargs: dict[str, Any] | None = None,
) -> Any:
    """Выполнить запрос с инициализацией сессии и обработкой ошибок.

    Аргументы:
    - `client` - Экземпляр клиента для взаимодействия.
    - `func` - Функция для выполнения запроса;
        первый аргумент - `IEventsProviderClient`.
    - `func_kwargs` - Параметры для функции `func`; по умолчанию None.
    - `on_success` - Функция для обработки успешного запроса;
        первый аргумент - результат выполнения `func`; по умолчанию None.
    - `on_success_kwargs` - Параметры для функции `on_success`;
        по умолчанию None.
    - `on_error` - Функция для обработки ошибки;
        первый аргумент - ошибка; по умолчанию None.
    - `on_error_kwargs` - Параметры для функции `on_error`;
        по умолчанию None.

    Возвращает:
    - Результат выполнения функции `on_success` или `func`
        если первая не задана.

    """
    try:
        async with client:
            result = await func(client, **(func_kwargs or {}))
    except (TimeoutError, ClientConnectionError, ClientResponseError) as e:
        if on_error is None:
            raise
        return await on_error(e, **(on_error_kwargs or {}))
    if on_success is None:
        return result
    return await on_success(result, **(on_success_kwargs or {}))


class EventsPaginator:
    """Пагинатор событий EventsProviderAPI.

    Для использования необходимо вызвать метод `__call__`.

    """

    def __call__(
        self, client: IEventsProviderClient, changed_at: date
    ) -> "EventsPaginator":
        """Установить параметры пагинатора.

        Аргументы:
        - `client`: `IEventsProviderClient` - Клиент для взаимодействия.
        - `changed_at` - Дата последнего изменения в ISO формате.

        """
        self._client = client
        self._changed_at = changed_at
        self._cursor = None
        self._events = []
        self._current = 0

        return self

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
            if not self._events:
                raise StopAsyncIteration
            self._current = 0
        event = self._events[self._current]
        self._current += 1
        return event


class EventsProviderParser:
    """Парсер данных EventsProviderAPI."""

    def parse_event_dict(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Разобрать событие и вернуть словари с преобразованными данными.

        Аргументы:
        - `data` - Словарь с данными события и места проведения.

        Возвращает:
        - Словарь с данными события и словарь с данными места проведения.

        """
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
        """Конвертировать даты в UTC."""
        for c in cls_.__table__.c:
            if isinstance(c.type, DateTime) and c.key in data:
                data[c.key] = datetime.fromisoformat(data[c.key]).astimezone(
                    UTC
                )
