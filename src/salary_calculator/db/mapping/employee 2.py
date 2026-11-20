"""Маппер EmployeeMapper."""

from salary_calculator.db.models import (
    EmployeeRow,
)
from salary_calculator.models import (
    Employee,
)


class EmployeeMapper:
    """Преобразует ORM-данные в предметные модели без открытой Session."""

    @staticmethod
    def to_domain(row: EmployeeRow) -> Employee:
        """Собирает кадровую карточку из ORM-ряда."""

        return Employee(
            row.employee_id,
            row.full_name,
            row.inn,
            row.position,
            row.hire_date,
            row.experience_years,
            row.rate_per_shift,
            row.dismissal_date,
        )

    @staticmethod
    def fields(employee: Employee) -> dict[str, object]:
        """Возвращает изменяемые поля карточки для записи в ORM-ряд."""

        return {
            "full_name": employee.full_name,
            "inn": employee.inn,
            "position": employee.position,
            "hire_date": employee.hire_date,
            "experience_years": employee.experience_years,
            "rate_per_shift": employee.rate_per_shift,
            "dismissal_date": employee.dismissal_date,
        }
