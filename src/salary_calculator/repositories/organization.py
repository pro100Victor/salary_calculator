"""Контракт хранения реквизитов организации."""

from abc import ABC, abstractmethod

from salary_calculator.models import Organization


class OrganizationRepository(ABC):
    """Определяет обязательные операции хранилища реквизитов."""

    @abstractmethod
    def get(self) -> Organization:
        """Возвращает реквизиты; при отсутствии поднимает LookupError."""

    @abstractmethod
    def save(self, organization: Organization) -> Organization:
        """Создаёт или обновляет единственные реквизиты предприятия."""


class InMemoryOrganizationRepository(OrganizationRepository):
    """Хранит реквизиты в переменной процесса."""

    def __init__(self) -> None:
        """Создаёт пустую конфигурацию предприятия."""

        self._organization: Organization | None = None

    def get(self) -> Organization:
        """Возвращает реквизиты или требует первоначальной настройки."""

        if self._organization is None:
            raise LookupError("сначала настройте организацию")
        return self._organization

    def save(self, organization: Organization) -> Organization:
        """Сохраняет реквизиты предприятия."""

        self._organization = organization
        return organization
