"""API синхронизации."""

from fastapi import APIRouter, status

from app.services import SyncService, scheduler

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Вызвать синхронизацию",
)
async def trigger():
    """Вызвать внеплановую синхронизацию данных."""
    SyncService(scheduler).trigger_job()
