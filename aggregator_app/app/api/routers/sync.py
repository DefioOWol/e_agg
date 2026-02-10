"""API синхронизации."""

from fastapi import APIRouter, status

from app.services.sync import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger():
    """Проверить работоспособность API."""
    sync_service.trigger_job()
