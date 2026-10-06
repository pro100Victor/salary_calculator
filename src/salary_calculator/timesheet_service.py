"""Формирование, заполнение и закрытие месячного табеля."""

from salary_calculator.calendar_service import CalendarService
from salary_calculator.contracts import TimesheetRepository
from salary_calculator.employee_service import EmployeeService
from salary_calculator.models import Period, Timesheet, TimesheetEntry


class TimesheetService:
    """Проверяет табель и сохраняет только корректные строки."""

    def __init__(
        self,
        repository: TimesheetRepository,
        employees: EmployeeService,
        calendar: CalendarService,
    ) -> None:
        """Подключает хранилище табелей, справочник и календарь."""

        self._repository = repository
        self._employees = employees
        self._calendar = calendar

    def generate(self, period: Period) -> Timesheet:
        """Создаёт табель для работавших в месяце либо открывает существующий."""

        if self._repository.contains(period):
            return self._repository.get(period)
        employee_ids = tuple(
            item.employee_id for item in self._employees.employed_in(period)
        )
        if not employee_ids:
            raise ValueError("за выбранный период нет сотрудников в штате")
        timesheet = Timesheet(period, self._calendar.get_norm(period), employee_ids)
        self._repository.save(timesheet)
        return timesheet

    def get(self, period: Period) -> Timesheet:
        """Возвращает ранее созданный табель."""

        return self._repository.get(period)

    def fill(
        self,
        period: Period,
        employee_id: int,
        worked_shifts: int,
        sick_days: int,
        vacation_days: int,
    ) -> TimesheetEntry:
        """Проверяет смены и отсутствия перед сохранением одной строки."""

        timesheet = self.get(period)
        if timesheet.closed:
            raise ValueError("расчётный период закрыт")
        if employee_id not in timesheet.employee_ids:
            raise ValueError("сотрудника нет в табеле выбранного периода")
        numbers = (worked_shifts, sick_days, vacation_days)
        if any(
            isinstance(number, bool) or not isinstance(number, int)
            for number in numbers
        ):
            raise ValueError("смены и дни должны быть целыми числами")
        if any(number < 0 for number in numbers):
            raise ValueError("смены и дни не могут быть отрицательными")
        entry = TimesheetEntry(employee_id, *numbers)
        if entry.total_days > timesheet.shift_norm:
            raise ValueError("сумма смен, больничного и отпуска превышает норму")
        if timesheet.entries.get(employee_id) != entry:
            timesheet.revision += 1
        timesheet.entries[employee_id] = entry
        return entry

    def close(self, period: Period) -> None:
        """Закрывает период только после актуального успешного расчёта."""

        timesheet = self.get(period)
        if timesheet.closed:
            raise ValueError("расчётный период уже закрыт")
        timesheet.closed = True
