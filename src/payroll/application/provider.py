"""Контракт сборки сервисов на одну команду CLI или HTTP-запрос."""

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager

from payroll.application.services import ApplicationServices


class ServiceProvider(ABC):
    """Позволяет заменить InMemory на SQL без изменения пользовательских форм."""

    @abstractmethod
    def operation(self) -> AbstractContextManager[ApplicationServices]:
        """Открывает операцию; SQL-реализация управляет Session и транзакцией."""

    @property
    @abstractmethod
    def storage_mode(self) -> str:
        """Возвращает честное название используемого хранилища."""
