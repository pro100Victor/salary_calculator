"""Компоненты расчёта начислений и НДФЛ."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol


MONEY_PRECISION = Decimal("0.01")


class SalaryCalculationStrategy(Protocol):
    """Определяет общий контракт для способов начисления зарплаты."""

    def calculate(self, rate_per_shift: float, worked_shifts: int) -> Decimal:
        """Возвращает начисленную сумму до удержания налога."""

        ...


class ShiftSalaryCalculator:
    """Рассчитывает начисление по ставке за одну смену."""

    def calculate(self, rate_per_shift: float, worked_shifts: int) -> Decimal:
        """Умножает ставку на фактически отработанные смены."""

        rate = Decimal(str(rate_per_shift))
        accrued = rate * worked_shifts
        return accrued.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


class TaxCalculator:
    """Рассчитывает фиксированный НДФЛ в размере 13 процентов."""

    NDFL_RATE = Decimal("0.13")

    def calculate(self, accrued: Decimal) -> Decimal:
        """Возвращает округлённую сумму удержанного НДФЛ."""

        tax = accrued * self.NDFL_RATE
        return tax.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)
