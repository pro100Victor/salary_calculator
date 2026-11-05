from decimal import ROUND_HALF_UP, Decimal

from salary_calculator.contracts import SalaryCalculationStrategy

KOPECK = Decimal("0.01")



class ShiftSalaryCalculator(SalaryCalculationStrategy):
    """Рассчитывает начисление по ставке за рабочую смену."""

    def calculate(self, rate_per_shift: Decimal, worked_shifts: int) -> Decimal:
        """Умножает ставку на фактически отработанные смены."""

        return (rate_per_shift * worked_shifts).quantize(KOPECK, rounding=ROUND_HALF_UP)