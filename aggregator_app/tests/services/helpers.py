"""Вспомогательные функции для тестов сервисов."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from app.orm.models import EventStatus, Member, SyncMeta, SyncStatus
from app.orm.repositories.event import IEventRepository
from app.orm.repositories.member import IMemberRepository
from app.orm.repositories.place import IPlaceRepository
from app.orm.repositories.sync_meta import ISyncMetaRepository
from app.orm.uow import IUnitOfWork
from app.services.events_provider import IEventsProviderClient


def get_raw_iso_datetime_now():
    return datetime.now(UTC).isoformat()


def get_raw_place():
    return {
        "id": str(uuid4()),
        "name": "Test hall",
        "city": "Test city",
        "address": "Test street 1",
        "seats_pattern": "A1-A10",
        "changed_at": get_raw_iso_datetime_now(),
        "created_at": get_raw_iso_datetime_now(),
    }


def get_raw_event(status=EventStatus.NEW):
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


def get_raw_member():
    return {
        "first_name": "First",
        "last_name": "Last",
        "email": "first.last@example.com",
        "seat": "A1",
    }


class FakeEventsProviderClient(IEventsProviderClient):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def get_events(self, changed_at, cursor=None):
        return self.kwargs["pages"][cursor]

    async def get_seats(self, event_id):
        return self.kwargs["seats"]

    async def register_member(self, event_id, member_data):
        return self.kwargs["ticket_id"]

    async def unregister_member(self, event_id, ticket_id):
        return {"success": True}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    @staticmethod
    def extract_cursor(response):
        return response["next"]


class FakeEventRepository(IEventRepository):
    def __init__(self, events=None):
        self.events = events or []

    def _get_events(self, filter_):
        events = self.events
        if filter_ and filter_.event_time__gte:
            event_time = filter_.event_time__gte
            event_time = datetime(
                event_time.year, event_time.month, event_time.day, tzinfo=UTC
            )
            events = [
                event for event in events if event.event_time >= event_time
            ]
        return events

    async def get_paginated(self, page, page_size, filter_=None):
        return self._get_events(filter_)

    async def get_by_id(self, event_id):
        return next(
            (event for event in self.events if event.id == event_id), None
        )

    async def get_count(self, filter_=None):
        return len(self._get_events(filter_))

    async def upsert(self, json_data_list):
        pass


class FakeMemberRepository(IMemberRepository):
    def __init__(self, members=None):
        self.members = members or {}

    async def create(self, json_data):
        member = Member(**json_data)
        self.members[member.ticket_id] = member
        return member

    async def get_by_id(self, ticket_id, *, load_event=False):
        return self.members.get(ticket_id)

    async def delete(self, ticket_id):
        return self.members.pop(ticket_id, None) is not None


class FakePlaceRepository(IPlaceRepository):
    async def upsert(self, json_data_list):
        pass


class FakeSyncMetaRepository(ISyncMetaRepository):
    def __init__(self, meta=None):
        self.meta = meta

    async def get_or_add(self, *, for_update=False):
        if self.meta is None:
            self.meta = SyncMeta(id=1, sync_status=SyncStatus.NEVER)
            return self.meta, True
        return self.meta, False


class FakeUnitOfWork(IUnitOfWork):
    def __init__(self):
        self.events = FakeEventRepository()
        self.members = FakeMemberRepository()
        self.places = FakePlaceRepository()
        self.sync_meta = FakeSyncMetaRepository()

        self._began = False
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        self.committed = False
        self.rolled_back = False
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.rollback()

    @asynccontextmanager
    async def begin(self):
        self._began = True
        try:
            yield self
        finally:
            await self.commit()
            self._began = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True
