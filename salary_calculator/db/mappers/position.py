"""Преобразование position без SQL-запросов и управления Session."""

from salary_calculator.db.models import PositionRow
from salary_calculator.models import Position


class PositionMapper:
    """Преобразует таблицу position и предметный объект."""

    @staticmethod
    def to_domain(row: PositionRow) -> Position:
        """Создаёт проверенный dataclass из загруженной записи."""
        return Position(row.name, row.base_rate, row.seniority_percent)

    @staticmethod
    def apply(value: Position, row: PositionRow) -> None:
        """Копирует предметные поля в существующую ORM-запись."""
        row.name = value.name
        row.base_rate = value.base_rate
        row.seniority_percent = value.seniority_percent
        row.name_key = value.name.strip().casefold()
