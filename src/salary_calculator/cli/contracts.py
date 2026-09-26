"""Контракты взаимодействия CLI с расчётной частью программы."""

from typing import Protocol, Sequence


class EmployeeView(Protocol):
    """Описывает данные сотрудника, необходимые интерфейсу."""

    employee_id: int
    full_name: str
    inn: str
    position: str
    rate_per_shift: float


class PayrollResultView(Protocol):
    """Описывает результат расчёта, необходимый интерфейсу."""

    employee: EmployeeView
    worked_shifts: int
    accrued: float
    tax: float
    amount_to_pay: float


class EmployeeServiceProtocol(Protocol):
    """Определяет методы сервиса сотрудников для работы CLI."""

    def add_employee(
        self,
        full_name: str,
        inn: str,
        position: str,
        rate_per_shift: float,
    ) -> EmployeeView:
        """Добавляет сотрудника и возвращает созданный объект."""

        ...

    def get_all_employees(self) -> Sequence[EmployeeView]:
        """Возвращает всех добавленных сотрудников."""

        ...

    def get_employee_by_id(self, employee_id: int) -> EmployeeView:
        """Возвращает сотрудника по идентификатору."""

        ...


class PayrollServiceProtocol(Protocol):
    """Определяет метод расчёта заработной платы для работы CLI."""

    def calculate(
        self,
        employee: EmployeeView,
        worked_shifts: int,
        shift_norm: int,
    ) -> PayrollResultView:
        """Рассчитывает зарплату сотрудника за указанный период."""

        ...
