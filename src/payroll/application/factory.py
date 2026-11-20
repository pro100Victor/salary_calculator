"""Единственное место выбора хранилища для CLI и веб-приложения."""

import os

from payroll.application.memory_provider import InMemoryServiceProvider
from payroll.application.provider import ServiceProvider
from payroll.application.sql_provider import SQLServiceProvider

DEFAULT_DATABASE_URL = "postgresql+psycopg://salary:salary@localhost:5432/salary"


def create_provider() -> ServiceProvider:
    """Возвращает SQL-провайдер; STORAGE_BACKEND=memory включает InMemory."""

    backend = os.environ.get("STORAGE_BACKEND", "postgres").strip().lower()
    if backend == "memory":
        return InMemoryServiceProvider()
    if backend in ("postgres", "postgresql"):
        return SQLServiceProvider(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
    raise RuntimeError(
        f"неизвестный STORAGE_BACKEND: {backend}; ожидается memory или postgres"
    )
