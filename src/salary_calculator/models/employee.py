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

    @staticmethod
    def validate_full_name(value: str) -> None:
        """Проверяет ФИО сотрудника."""
        if not value.strip():
            raise ValueError("ФИО не должно быть пустым")

    @staticmethod
    def validate_dates(hire_date: date, dismissal_date: date | None = None) -> None:
        """Проверяет типы дат и единственное правило их взаимного порядка."""

        if not isinstance(hire_date, date):
            raise ValueError("введите корректную дату приёма")
        if dismissal_date is not None:
            if not isinstance(dismissal_date, date):
                raise ValueError("введите корректную дату увольнения")
            if dismissal_date < hire_date:
                raise ValueError("увольнение не может быть раньше приёма на работу")

    @staticmethod
    def validate_experience_years(value: int) -> None:
        """Проверяет стаж в полных годах."""
        if type(value) is not int or not 0 <= value <= 80:
            raise ValueError("стаж должен быть целым числом от 0 до 80 лет")

    def __post_init__(self) -> None:
        """Проверяет поля при создании карточки."""
        self.validate_full_name(self.full_name)
        self.validate_inn(self.inn)
        self.validate_dates(self.hire_date, self.dismissal_date)
        self.validate_experience_years(self.experience_years)

    @property
    def status(self) -> str:
        """Показывает, числится ли сотрудник в штате сейчас."""

        return "Уволен" if self.dismissal_date else "В штате"

    def employed_in(self, period: Period) -> bool:
        """Проверяет пересечение периода с датами работы сотрудника."""

        return self.hire_date <= period.end and (
            self.dismissal_date is None or self.dismissal_date >= period.start
        )
