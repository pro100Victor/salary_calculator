from dataclasses import dataclass
from decimal import Decimal

from .employee import Employee


@dataclass(frozen=True)
class PayrollResult:
    """Содержит результат расчёта зарплаты одного сотрудника."""

    employee: Employee
    worked_shifts: int
    sick_days: int
    vacation_days: int
    accrued: Decimal
    tax: Decimal
    amount_to_pay: Decimal