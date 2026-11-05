from dataclasses import dataclass


@dataclass(frozen=True)
class TimesheetEntry:
    """Содержит заполненную строку табеля одного сотрудника."""

    employee_id: int
    worked_shifts: int
    sick_days: int
    vacation_days: int

    @property
    def total_days(self) -> int:
        """Возвращает сумму смен и дней отсутствия."""

        return self.worked_shifts + self.sick_days + self.vacation_days