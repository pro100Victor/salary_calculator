"""Основные модели предметной области."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Employee:
    """Хранит сведения о сотруднике малого предприятия."""

    employee_id: int
    full_name: str
    inn: str
    position: str
    rate_per_shift: float


@dataclass(frozen=True, slots=True)
class PayrollResult:
    """Хранит результат расчёта зарплаты одного сотрудника."""

    employee: Employee
    worked_shifts: int
    accrued: float
    tax: float
    amount_to_pay: float
