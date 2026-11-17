"""Снимок карточки не зависит от сегодняшних данных сотрудника."""

from salary_calculator.db.models import PayrollResultRow
from salary_calculator.models import Employee, PayrollResult


class PayrollResultMapper:
    """Сохраняет исторические поля карточки вместе с точными суммами."""

    @staticmethod
    def to_domain(row: PayrollResultRow) -> PayrollResult:
        """Читает Employee из снимка, не из relationship employee."""
        employee = Employee(
            row.employee_id,
            row.full_name,
            row.inn,
            row.position_name,
            row.hire_date,
            row.experience_years,
            row.rate_per_shift,
            row.dismissal_date,
        )
        return PayrollResult(
            employee,
            row.worked_shifts,
            row.sick_days,
            row.vacation_days,
            row.accrued,
            row.tax,
            row.amount_to_pay,
        )

    @staticmethod
    def apply(value: PayrollResult, row: PayrollResultRow) -> None:
        """Переносит снимок карточки и результат готового расчёта."""
        employee = value.employee
        row.employee_id = employee.employee_id
        row.full_name = employee.full_name
        row.inn = employee.inn
        row.position_name = employee.position
        row.hire_date = employee.hire_date
        row.dismissal_date = employee.dismissal_date
        row.experience_years = employee.experience_years
        row.rate_per_shift = employee.rate_per_shift
        row.worked_shifts = value.worked_shifts
        row.sick_days = value.sick_days
        row.vacation_days = value.vacation_days
        row.accrued = value.accrued
        row.tax = value.tax
        row.amount_to_pay = value.amount_to_pay
