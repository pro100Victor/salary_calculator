"""Преобразование календарных колонок в расчётный период."""

from payroll.models import Period


class PeriodMapper:
    """Собирает объект периода из колонок шапки табеля или ведомости."""

    @staticmethod
    def to_domain(year: int, month: int) -> Period:
        """Проверяет календарный месяц через предметную модель."""

        return Period(year, month)
