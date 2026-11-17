"""Единственное место выбора хранилища для CLI и веб-приложения."""

from salary_calculator.application.memory_provider import InMemoryServiceProvider
from salary_calculator.application.provider import ServiceProvider


def create_provider() -> ServiceProvider:
    """Пока собирает InMemory; SQL-провайдер подключает инженер 3 после миграций."""

    return InMemoryServiceProvider()
