from abc import ABC, abstractmethod
from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from salary_calculator.db.mappers.employee import EmployeeMapper
from salary_calculator.db.models import EmployeeRow
from salary_calculator.models import Employee
from salary_calculator.repositories.position import SQLAlchemyPositionRepository


class EmployeeRepository(ABC):
    """Определяет обязательные операции хранилища сотрудников."""

    @abstractmethod
    def add(self, employee: Employee) -> Employee:
        """Создаёт карточку и возвращает её с назначенным хранилищем ID."""

    @abstractmethod
    def save(self, employee: Employee) -> None:
        """Сохраняет новую или изменённую кадровую карточку."""

    @abstractmethod
    def get(self, employee_id: int) -> Employee:
        """Находит сотрудника по идентификатору."""

    @abstractmethod
    def list_all(self) -> list[Employee]:
        """Возвращает все карточки сотрудников."""


class InMemoryEmployeeRepository(EmployeeRepository):
    """Хранит кадровые карточки в словаре по идентификатору."""

    def __init__(self) -> None:
        """Создаёт пустой справочник."""

        self._items: dict[int, Employee] = {}

    def add(self, employee: Employee) -> Employee:
        """Назначает локальный ID только для InMemory-реализации."""
        employee = replace(employee, employee_id=max(self._items, default=0) + 1)
        self.save(employee)
        return employee

    def save(self, employee: Employee) -> None:
        """Добавляет или заменяет карточку сотрудника."""

        self._items[employee.employee_id] = employee

    def get(self, employee_id: int) -> Employee:
        """Находит сотрудника по его ID."""

        try:
            return self._items[employee_id]
        except KeyError as error:
            raise LookupError(f"сотрудник с ID {employee_id} не найден") from error

    def list_all(self) -> list[Employee]:
        """Возвращает список всех сотрудников."""

        return list(self._items.values())


class SQLAlchemyEmployeeRepository(EmployeeRepository):
    """Сохраняет карточки; PostgreSQL назначает ID при flush."""

    def __init__(self, session: Session) -> None:
        """Получает Session внешней транзакции."""
        self._session = session

    def add(self, employee: Employee) -> Employee:
        """Не передаёт временный employee_id в первичный ключ БД."""
        row = EmployeeRow(organization_id=1)
        row.position = SQLAlchemyPositionRepository(self._session).get_row(
            employee.position
        )
        EmployeeMapper.apply(employee, row)
        self._session.add(row)
        self._session.flush()
        return EmployeeMapper.to_domain(row)

    def save(self, employee: Employee) -> None:
        """Обновляет существующую карточку, сохраняя её идентификатор."""
        row = self._session.get(EmployeeRow, employee.employee_id, with_for_update=True)
        if row is None:
            raise LookupError(f"сотрудник с ID {employee.employee_id} не найден")
        row.position = SQLAlchemyPositionRepository(self._session).get_row(
            employee.position
        )
        EmployeeMapper.apply(employee, row)
        self._session.flush()

    def get(self, employee_id: int) -> Employee:
        """Загружает должность до выхода из Session."""
        row = self._session.scalar(
            select(EmployeeRow)
            .options(joinedload(EmployeeRow.position))
            .where(EmployeeRow.id == employee_id, EmployeeRow.organization_id == 1)
        )
        if row is None:
            raise LookupError(f"сотрудник с ID {employee_id} не найден")
        return EmployeeMapper.to_domain(row)

    def list_all(self) -> list[Employee]:
        """Читает карточки с должностями одним запросом."""
        rows = self._session.scalars(
            select(EmployeeRow)
            .options(joinedload(EmployeeRow.position))
            .where(EmployeeRow.organization_id == 1)
            .order_by(EmployeeRow.id)
        )
        return [EmployeeMapper.to_domain(row) for row in rows]
