"""Healthcheck API."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def healthcheck():
    """Проверить работоспособность API."""
    return {"status": "ok"}
