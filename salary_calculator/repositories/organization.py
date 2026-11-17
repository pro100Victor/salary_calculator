"""Контракт и реализации хранения реквизитов одной организации."""

from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.orm import Session

from salary_calculator.db.mappers.organization import OrganizationMapper
from salary_calculator.db.models import OrganizationRow
from salary_calculator.models import Organization


class OrganizationRepository(ABC):
    """Хранит реквизиты установки без управления транзакциями."""

    @abstractmethod
    def get(self) -> Organization:
        """Возвращает настроенное предприятие или LookupError."""

    @abstractmethod
    def save(self, value: Organization) -> None:
        """Сохраняет реквизиты в текущей операции."""


class InMemoryOrganizationRepository(OrganizationRepository):
    """Сохраняет реквизиты до остановки процесса."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище."""
        self._value: Organization | None = None

    def get(self) -> Organization:
        """Возвращает реквизиты либо ошибку отсутствия настройки."""
        if self._value is None:
            raise LookupError("сначала настройте организацию")
        return self._value

    def save(self, value: Organization) -> None:
        """Заменяет реквизиты установки."""
        self._value = value


class SQLAlchemyOrganizationRepository(OrganizationRepository):
    """Использует переданную Session без commit/rollback."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""
        self._session = session

    def get(self) -> Organization:
        """Восстанавливает самостоятельные реквизиты."""
        row = self._session.get(OrganizationRow, 1)
        if row is None:
            raise LookupError("сначала настройте организацию")
        return OrganizationMapper.to_domain(row)

    def save(self, value: Organization) -> None:
        """Обновляет единственную организацию, не стирая связанные данные."""
        row = self._session.scalar(
            select(OrganizationRow).where(OrganizationRow.id == 1).with_for_update()
        )
        if row is None:
            row = OrganizationRow(id=1)
            self._session.add(row)
        OrganizationMapper.apply(value, row)
        self._session.flush()
