"""Утилиты и вспомогательные элементы сервисов."""

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from datetime import UTC
from typing import Any, Protocol, Self

from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone=UTC)


class IExternalClient(AbstractAsyncContextManager[Self], Protocol):
    """Интерфейс клиента для взаимодействия с внешними сервисами."""


async def with_external_client(
    client: IExternalClient,
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
            первый аргумент - `IExternalClient`.
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
