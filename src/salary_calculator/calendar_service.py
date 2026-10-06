"""Определение нормы смен для произвольного малого предприятия."""

from calendar import monthrange
from datetime import date

from salary_calculator.models import Period


class CalendarService:
    """Считает будни и позволяет явно задать норму по графику предприятия."""

    def __init__(self) -> None:
        """Создаёт словарь нормативов по расчётным периодам."""

        self._overrides: dict[Period, int] = {}

    def set_norm(self, period: Period, shifts: int) -> None:
        """Задаёт норму смен на месяц для конкретной организации."""

        max_days = monthrange(period.year, period.month)[1]
        if (
            isinstance(shifts, bool)
            or not isinstance(shifts, int)
            or not 1 <= shifts <= max_days
        ):
            raise ValueError(f"норма смен должна быть от 1 до {max_days}")
        self._overrides[period] = shifts

    def get_norm(self, period: Period) -> int:
        """Возвращает введённую норму либо число будней без праздников."""

        if period in self._overrides:
            return self._overrides[period]
        days = monthrange(period.year, period.month)[1]
        return sum(
            date(period.year, period.month, day).weekday() < 5
            for day in range(1, days + 1)
        )
