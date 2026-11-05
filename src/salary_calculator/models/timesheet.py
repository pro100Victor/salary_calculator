from dataclasses import dataclass, field

from .period import Period
from .timesheet_entry import TimesheetEntry


@dataclass
class Timesheet:
    """Хранит InMemory-табель за расчётный месяц."""

    period: Period
    shift_norm: int
    employee_ids: tuple[int, ...]
    entries: dict[int, TimesheetEntry] = field(default_factory=dict)
    revision: int = 0
    closed: bool = False

    def validate_days(self, value: int, used_days: int = 0) -> None:
        """Проверяет количество дней с учётом уже распределённой нормы."""

        if type(value) is not int:
            raise ValueError("смены и дни должны быть целыми числами")
        if value < 0:
            raise ValueError("смены и дни не могут быть отрицательными")
        if used_days + value > self.shift_norm:
            raise ValueError("сумма смен, больничного и отпуска превышает норму")