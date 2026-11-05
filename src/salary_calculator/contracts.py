"""Явные абстрактные интерфейсы для расчёта и InMemory-хранилищ."""

from abc import ABC, abstractmethod
from decimal import Decimal


class SalaryCalculationStrategy(ABC):
    """Требует от схемы оплаты реализации расчёта начисления."""

    @abstractmethod
    def calculate(self, rate_per_shift: Decimal, worked_shifts: int) -> Decimal:
        """Рассчитывает начисление до удержания НДФЛ."""