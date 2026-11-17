"""Преобразование period без SQL-запросов и управления Session."""

from salary_calculator.db.models import PeriodRow
from salary_calculator.models import Period


class PeriodMapper:
    """Преобразует таблицу period и предметный объект."""

    @staticmethod
    def to_domain(row: PeriodRow) -> Period:
        """Создаёт проверенный dataclass из загруженной записи."""
        return Period(row.year, row.month)

    @staticmethod
    def apply(value: Period, row: PeriodRow) -> None:
        """Копирует предметные поля в существующую ORM-запись."""
        row.year = value.year
        row.month = value.month
