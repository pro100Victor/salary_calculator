from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .period import Period


@dataclass(frozen=True)
class Employee:
    """Хранит кадровую карточку и рассчитанную ставку за смену."""

    employee_id: int
    full_name: str
    inn: str
    position: str
    hire_date: date
    experience_years: int
    rate_per_shift: Decimal
    dismissal_date: date | None = None

    @staticmethod
    def validate_inn(inn: str) -> None:
        """Проверяет формат ИНН сотрудника."""

        if len(inn) != 12 or not inn.isascii() or not inn.isdigit():
            raise ValueError("ИНН сотрудника должен содержать 12 цифр")

    def __post_init__(self) -> None:
        """Проверяет ИНН при создании карточки."""

        self.validate_inn(self.inn)

    @property
    def status(self) -> str:
        """Показывает, числится ли сотрудник в штате сейчас."""

        return "Уволен" if self.dismissal_date else "В штате"

    def employed_in(self, period: Period) -> bool:
        """Проверяет пересечение периода с датами работы сотрудника."""

        return self.hire_date <= period.end and (
            self.dismissal_date is None or self.dismissal_date >= period.start
        )