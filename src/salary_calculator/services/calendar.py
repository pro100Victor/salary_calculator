"""Определение нормы смен для произвольного малого предприятия."""

from calendar import monthrange
from datetime import date

from salary_calculator.models import Period
from salary_calculator.repositories.norm import InMemoryNormRepository, NormRepository


class CalendarService:
    """Считает будни и позволяет явно задать норму по графику предприятия."""

    def __init__(self, repository: NormRepository | None = None) -> None:
        """Принимает хранилище ручных норм, по умолчанию InMemory."""

        self._repository = (
            repository if repository is not None else InMemoryNormRepository()
        )

    def set_norm(self, period: Period, shifts: int) -> None:
        """Задаёт норму смен на месяц."""

        self.validate_norm(period, shifts)
        self._repository.save(period, shifts)

    @staticmethod
    def validate_norm(period: Period, shifts: int) -> None:
        """Проверяет норму без изменения настроек календаря."""

        max_days = period.end.day
        if type(shifts) is not int or not 1 <= shifts <= max_days:
            raise ValueError(f"норма смен должна быть от 1 до {max_days}")

    def get_norm(self, period: Period) -> int:
        """Возвращает введённую норму либо число будней без праздников."""

        override = self._repository.get(period)
        if override is not None:
            return override
        days = monthrange(period.year, period.month)[1]
        return sum(
            date(period.year, period.month, day).weekday() < 5
            for day in range(1, days + 1)
        )
