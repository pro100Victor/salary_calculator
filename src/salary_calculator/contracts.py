"""Явные абстрактные интерфейсы для расчёта и InMemory-хранилищ."""

from abc import ABC, abstractmethod
from decimal import Decimal

from salary_calculator.models import Employee, PayrollStatement, Period, Timesheet


class SalaryCalculationStrategy(ABC):
    """Требует от схемы оплаты реализации расчёта начисления."""

    @abstractmethod
    def calculate(self, rate_per_shift: Decimal, worked_shifts: int) -> Decimal:
        """Рассчитывает начисление до удержания НДФЛ."""


class EmployeeRepository(ABC):
    """Определяет обязательные операции хранилища сотрудников."""

    @abstractmethod
    def save(self, employee: Employee) -> None:
        """Сохраняет новую или изменённую кадровую карточку."""

    @abstractmethod
    def get(self, employee_id: int) -> Employee:
        """Находит сотрудника по идентификатору."""

    @abstractmethod
    def list_all(self) -> list[Employee]:
        """Возвращает все карточки сотрудников."""


class TimesheetRepository(ABC):
    """Определяет обязательные операции хранилища табелей."""

    @abstractmethod
    def save(self, timesheet: Timesheet) -> None:
        """Сохраняет табель за один месяц."""

    @abstractmethod
    def get(self, period: Period) -> Timesheet:
        """Возвращает табель за выбранный месяц."""

    @abstractmethod
    def contains(self, period: Period) -> bool:
        """Проверяет существование табеля за выбранный месяц."""


class StatementRepository(ABC):
    """Определяет обязательные операции хранилища ведомостей."""

    @abstractmethod
    def save(self, statement: PayrollStatement) -> None:
        """Сохраняет проверенную расчётную ведомость."""

    @abstractmethod
    def get(self, period: Period) -> PayrollStatement:
        """Возвращает ведомость за выбранный месяц."""

    @abstractmethod
    def contains(self, period: Period) -> bool:
        """Проверяет наличие ранее сформированной ведомости."""
