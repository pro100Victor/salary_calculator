"""Преобразование исторического снимка расчётного листка."""

from salary_calculator.db.models import StatementResultRow
from salary_calculator.models import Employee, PayrollResult


class PayrollResultMapper:
    """Читает снимок карточки, не подменяя его текущим сотрудником."""

    @staticmethod
    def to_domain(row: StatementResultRow) -> PayrollResult:
        """Собирает персональный расчёт из строки ведомости."""

        snapshot = Employee(
            row.employee_id,
            row.full_name,
            row.inn,
            row.position,
            row.hire_date,
            row.experience_years,
            row.rate_per_shift,
            row.dismissal_date,
        )
        return PayrollResult(
            snapshot,
            row.worked_shifts,
            row.sick_days,
            row.vacation_days,
            row.accrued,
            row.tax,
            row.amount_to_pay,
        )

    @staticmethod
    def fields(result: PayrollResult) -> dict[str, object]:
        """Возвращает поля строки ведомости для записи в ORM-ряд."""

        return {
            "full_name": result.employee.full_name,
            "inn": result.employee.inn,
            "position": result.employee.position,
            "hire_date": result.employee.hire_date,
            "experience_years": result.employee.experience_years,
            "rate_per_shift": result.employee.rate_per_shift,
            "dismissal_date": result.employee.dismissal_date,
            "worked_shifts": result.worked_shifts,
            "sick_days": result.sick_days,
            "vacation_days": result.vacation_days,
            "accrued": result.accrued,
            "tax": result.tax,
            "amount_to_pay": result.amount_to_pay,
        }
