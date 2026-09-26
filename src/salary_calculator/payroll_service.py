"""Сервис расчёта заработной платы."""

from decimal import ROUND_HALF_UP

from salary_calculator.calculators import (
    MONEY_PRECISION,
    SalaryCalculationStrategy,
    ShiftSalaryCalculator,
    TaxCalculator,
)
from salary_calculator.models import Employee, PayrollResult


class PayrollService:
    """Проверяет табельные данные и формирует результат расчёта."""

    def __init__(
        self,
        salary_calculator: SalaryCalculationStrategy | None = None,
        tax_calculator: TaxCalculator | None = None,
    ) -> None:
        """Подключает расчёт по сменам и фиксированный расчёт НДФЛ."""

        self._salary_calculator = salary_calculator or ShiftSalaryCalculator()
        self._tax_calculator = tax_calculator or TaxCalculator()

    def calculate(
        self,
        employee: Employee,
        worked_shifts: int,
        shift_norm: int,
    ) -> PayrollResult:
        """Рассчитывает начисление, НДФЛ и сумму к выплате."""

        self._validate_shift_norm(shift_norm)
        self._validate_worked_shifts(worked_shifts, shift_norm)

        accrued = self._salary_calculator.calculate(
            rate_per_shift=employee.rate_per_shift,
            worked_shifts=worked_shifts,
        )
        tax = self._tax_calculator.calculate(accrued)
        amount_to_pay = (accrued - tax).quantize(
            MONEY_PRECISION,
            rounding=ROUND_HALF_UP,
        )

        return PayrollResult(
            employee=employee,
            worked_shifts=worked_shifts,
            accrued=float(accrued),
            tax=float(tax),
            amount_to_pay=float(amount_to_pay),
        )

    def _validate_shift_norm(self, shift_norm: int) -> None:
        """Проверяет календарную норму смен за месяц."""

        if isinstance(shift_norm, bool) or not isinstance(shift_norm, int):
            raise ValueError("норма смен должна быть целым числом")

        if shift_norm <= 0:
            raise ValueError("норма смен должна быть больше нуля")

    def _validate_worked_shifts(
        self,
        worked_shifts: int,
        shift_norm: int,
    ) -> None:
        """Проверяет фактически отработанное количество смен."""

        if isinstance(worked_shifts, bool) or not isinstance(worked_shifts, int):
            raise ValueError("количество смен должно быть целым числом")

        if worked_shifts < 0:
            raise ValueError("количество смен не может быть отрицательным")

        if worked_shifts > shift_norm:
            raise ValueError("количество смен не может превышать норму")
