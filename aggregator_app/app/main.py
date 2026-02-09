"""Основной модуль приложения."""

from fastapi import FastAPI

from app.api.routers import healthcheck

app = FastAPI(
    title="Events aggregator API",
    description="API for events aggregator",
    version="1.0.0",
    root_path="/api",
)

app.include_router(healthcheck.router)
