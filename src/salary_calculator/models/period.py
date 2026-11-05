from calendar import monthrange
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, order=True)
class Period:
    """Обозначает календарный месяц расчёта."""

    year: int
    month: int

    def __post_init__(self) -> None:
        """Проверяет год и месяц при создании периода."""

        self.validate_year(self.year)
        self.validate_month(self.month)

    @staticmethod
    def validate_year(value: int) -> None:
        """Проверяет год расчётного периода."""

        if type(value) is not int or not 1 <= value <= 9999:
            raise ValueError("год должен быть целым числом от 1 до 9999")

    @staticmethod
    def validate_month(value: int) -> None:
        """Проверяет месяц расчётного периода."""

        if type(value) is not int or not 1 <= value <= 12:
            raise ValueError("месяц должен быть целым числом от 1 до 12")

    @property
    def start(self) -> date:
        """Возвращает первый день месяца."""

        return date(self.year, self.month, 1)

    @property
    def end(self) -> date:
        """Возвращает последний день месяца."""

        return date(self.year, self.month, monthrange(self.year, self.month)[1])

    def __str__(self) -> str:
        """Представляет период в формате ММ.ГГГГ."""

        return f"{self.month:02d}.{self.year}"