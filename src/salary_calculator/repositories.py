"""Словари и списки для хранения данных только на время работы процесса."""

from salary_calculator.contracts import (
    EmployeeRepository,
    StatementRepository,
    TimesheetRepository,
)
from salary_calculator.models import Employee, PayrollStatement, Period, Timesheet


class InMemoryEmployeeRepository(EmployeeRepository):
    """Хранит кадровые карточки в словаре по идентификатору."""

    def __init__(self) -> None:
        """Создаёт пустой справочник."""

        self._items: dict[int, Employee] = {}

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


class InMemoryTimesheetRepository(TimesheetRepository):
    """Хранит месячные табели в словаре по периоду."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище табелей."""

        self._items: dict[Period, Timesheet] = {}

    def save(self, timesheet: Timesheet) -> None:
        """Сохраняет табель в оперативной памяти."""

        self._items[timesheet.period] = timesheet

    def get(self, period: Period) -> Timesheet:
        """Возвращает существующий табель."""

        try:
            return self._items[period]
        except KeyError as error:
            raise LookupError(f"табель за {period} не найден") from error

    def contains(self, period: Period) -> bool:
        """Сообщает, существует ли табель за период."""

        return period in self._items


class InMemoryStatementRepository(StatementRepository):
    """Хранит ведомости в оперативной памяти по месяцам."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище ведомостей."""

        self._items: dict[Period, PayrollStatement] = {}

    def save(self, statement: PayrollStatement) -> None:
        """Сохраняет подтверждённую ведомость."""

        self._items[statement.period] = statement

    def get(self, period: Period) -> PayrollStatement:
        """Возвращает ведомость за расчётный месяц."""

        try:
            return self._items[period]
        except KeyError as error:
            raise LookupError(f"ведомость за {period} не найдена") from error

    def contains(self, period: Period) -> bool:
        """Сообщает, существует ли ведомость за период."""

        return period in self._items
