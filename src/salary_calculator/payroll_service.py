"""Атомарное формирование расчётной ведомости по заполненному табелю."""

from salary_calculator.calculators import ShiftSalaryCalculator, TaxCalculator
from salary_calculator.contracts import SalaryCalculationStrategy, StatementRepository
from salary_calculator.employee_service import EmployeeService
from salary_calculator.models import PayrollResult, PayrollStatement, Period
from salary_calculator.organization_service import OrganizationService
from salary_calculator.timesheet_service import TimesheetService


class PayrollService:
    """Вычисляет зарплату каждого сотрудника и сохраняет ведомость целиком."""

    def __init__(
        self,
        statements: StatementRepository,
        timesheets: TimesheetService,
        employees: EmployeeService,
        organization: OrganizationService,
        strategy: SalaryCalculationStrategy | None = None,
    ) -> None:
        """Получает хранилища и абстрактную стратегию начисления."""

        self._statements = statements
        self._timesheets = timesheets
        self._employees = employees
        self._organization = organization
        self._strategy = strategy or ShiftSalaryCalculator()
        self._tax_calculator = TaxCalculator()

    def calculate_period(
        self, period: Period, replace_existing: bool = False
    ) -> PayrollStatement:
        """Считает готовый табель и заменяет прежний результат только при успехе."""

        timesheet = self._timesheets.get(period)
        if timesheet.closed:
            raise ValueError("закрытый период пересчитывать нельзя")
        if self._statements.contains(period) and not replace_existing:
            raise ValueError("ведомость уже существует; подтвердите перерасчёт")

        missing = set(timesheet.employee_ids) - set(timesheet.entries)
        if missing:
            raise ValueError(
                f"не заполнены строки сотрудников: {', '.join(map(str, sorted(missing)))}"
            )

        organization = self._organization.get_organization()
        results: list[PayrollResult] = []
        for employee_id in timesheet.employee_ids:
            employee = self._employees.get_employee_by_id(employee_id)
            entry = timesheet.entries[employee_id]
            accrued = self._strategy.calculate(
                employee.rate_per_shift, entry.worked_shifts
            )
            tax = self._tax_calculator.calculate(accrued)
            results.append(
                PayrollResult(
                    employee,
                    entry.worked_shifts,
                    entry.sick_days,
                    entry.vacation_days,
                    accrued,
                    tax,
                    accrued - tax,
                )
            )

        statement = PayrollStatement(
            period, organization.name, tuple(results), timesheet.revision
        )
        self._statements.save(statement)
        return statement

    def get_statement(self, period: Period) -> PayrollStatement:
        """Возвращает последнюю подтверждённую ведомость."""

        return self._statements.get(period)

    def is_current(self, period: Period) -> bool:
        """Проверяет соответствие ведомости текущей версии табеля."""

        statement = self.get_statement(period)
        return statement.source_revision == self._timesheets.get(period).revision

    def get_payslip(self, period: Period, employee_id: int) -> PayrollResult:
        """Возвращает персональный результат из ведомости за период."""

        statement = self.get_statement(period)
        for result in statement.results:
            if result.employee.employee_id == employee_id:
                return result
        raise LookupError(f"расчётного листка сотрудника {employee_id} нет")

    def close_period(self, period: Period) -> None:
        """Закрывает период при наличии актуальной ведомости."""

        self.get_statement(period)
        if not self.is_current(period):
            raise ValueError("после изменения табеля пересчитайте ведомость")
        self._timesheets.close(period)
