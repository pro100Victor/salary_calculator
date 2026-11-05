from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Position:
    """Задаёт базовую ставку и надбавку за полный год стажа."""

    name: str
    base_rate: Decimal
    seniority_percent: Decimal