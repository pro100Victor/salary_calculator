from dataclasses import dataclass


@dataclass(frozen=True)
class TimesheetEntry:
    """Содержит заполненную строку табеля одного сотрудника."""

    employee_id: int
    worked_shifts: int
    sick_days: int
    vacation_days: int

    @staticmethod
    def validate_day_count(value: int) -> None:
        """Проверяет число смен или дней отсутствия."""
        if type(value) is not int:
            raise ValueError("смены и дни должны быть целыми числами")
        if value < 0:
            raise ValueError("смены и дни не могут быть отрицательными")

    def __post_init__(self) -> None:
        """Проверяет значения строки табеля."""
        self.validate_day_count(self.worked_shifts)
        self.validate_day_count(self.sick_days)
        self.validate_day_count(self.vacation_days)

    @property
    def total_days(self) -> int:
        """Возвращает сумму смен и дней отсутствия."""

        return self.worked_shifts + self.sick_days + self.vacation_days