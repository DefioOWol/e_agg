"""Основной модуль приложения."""

from fastapi import FastAPI

app = FastAPI(
    title="Events aggregator API",
    description="API for events aggregator",
    version="1.0.0",
)
