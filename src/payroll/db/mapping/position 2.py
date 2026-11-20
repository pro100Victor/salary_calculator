"""Маппер PositionMapper."""

from payroll.db.models import (
    PositionRow,
)
from payroll.models import (
    Position,
)


class PositionMapper:
    """Преобразует ORM-данные в предметные модели без открытой Session."""

    @staticmethod
    def to_domain(row: PositionRow) -> Position:
        """Собирает доменную модель должности из ORM-ряда."""

        return Position(row.name, row.base_rate, row.seniority_percent)
