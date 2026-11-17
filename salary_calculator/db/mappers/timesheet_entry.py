"""Отсутствие ввода отличается от трёх введённых нулей."""

from salary_calculator.db.models import TimesheetEntryRow
from salary_calculator.models import TimesheetEntry


class TimesheetEntryMapper:
    """Преобразует заполненную строку; NULL остаётся отсутствием ввода."""

    @staticmethod
    def to_domain(row: TimesheetEntryRow) -> TimesheetEntry | None:
        """Возвращает None только для полностью незаполненной строки."""
        if row.worked_shifts is None:
            return None
        if row.sick_days is None or row.vacation_days is None:
            raise ValueError("повреждена строка табеля")
        return TimesheetEntry(
            row.employee_id, row.worked_shifts, row.sick_days, row.vacation_days
        )

    @staticmethod
    def apply(value: TimesheetEntry | None, row: TimesheetEntryRow) -> None:
        """Записывает заполненную строку либо явное отсутствие ввода."""
        row.worked_shifts = value.worked_shifts if value else None
        row.sick_days = value.sick_days if value else None
        row.vacation_days = value.vacation_days if value else None
