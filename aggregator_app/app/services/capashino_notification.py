"""Модуль взаимодействия с сервисом уведомлений."""

from typing import Any, Protocol

import backoff
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectionError

from app.config import settings
from app.orm.models.outbox import Outbox
from app.services.utils import IExternalClient


class INotificationClient(IExternalClient, Protocol):
    """Интерфейс клиента уведомлений."""

    async def notify(self, item: Outbox) -> dict[str, Any]:
        """Отправить уведомление с переданным телом запроса."""

    def get_body_from_outbox(self, item: Outbox) -> dict[str, Any]:
        """Получить тело запроса из outbox."""


class CapashinoNotificationClient(INotificationClient):
    """Клиент для взаимодействия с Capashino API.

    Реализует `INotificationClient`.

    """

    _BACKOFF_ON_EXCEPTION = backoff.on_exception(
        backoff.expo,
        (TimeoutError, ClientConnectionError),
        max_tries=3,
    )

    def __init__(self, total_timeout: int = 60, connect_timeout: int = 15):
        """Инициализировать клиент.

        Аргументы:
        - `total_timeout` - Максимальное время ожидания всего запроса;
            по умолчанию 60 секунд.
        - `connect_timeout` - Максимальное время ожидания соединения;
            по умолчанию 15 секунд.

        """
        self._timeout = ClientTimeout(
            total=total_timeout, connect=connect_timeout
        )
        self._session: ClientSession | None = None

    @_BACKOFF_ON_EXCEPTION
    async def notify(self, item: Outbox) -> dict[str, Any]:
        url = "/api/notifications"
        body = self.get_body_from_outbox(item)
        async with self._session.post(url, json=body) as response:
            return await response.json()

    def get_body_from_outbox(self, item: Outbox) -> dict[str, Any]:
        payload = item.payload
        return {
            "message": (
                f"Регистрация на мероприятие {payload['event_id']}"
                f" с местом {payload['seat']} успешна."
            ),
            "reference_id": payload["ticket_id"],
            "idempotency_key": f"register-{item.id}-{item.created_at}",
        }

    async def __aenter__(self):
        self._session = ClientSession(
            settings.capashino_base_url,
            headers={
                "Content-Type": "application/json",
                "X-API-key": settings.lms_api_key.get_secret_value(),
            },
            timeout=self._timeout,
            raise_for_status=True,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._session.close()
        self._session = None
