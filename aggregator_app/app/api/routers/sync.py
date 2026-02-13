"""API синхронизации."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.services.sync import SyncService, get_sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Вызвать синхронизацию",
)
async def trigger(
    sync_service: Annotated[SyncService, Depends(get_sync_service)],
):
    """Вызвать внеплановую синхронизацию данных."""
    sync_service.trigger_job()
