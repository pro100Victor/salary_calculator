"""Ставка хранится в карточке, актуальное имя должности берётся из связи."""

from salary_calculator.db.models import EmployeeRow
from salary_calculator.models import Employee


class EmployeeMapper:
    """Преобразует кадровую карточку без передачи ORM в интерфейс."""

    @staticmethod
    def to_domain(row: EmployeeRow) -> Employee:
        """Создаёт самостоятельную карточку с загруженной должностью."""
        return Employee(
            row.id,
            row.full_name,
            row.inn,
            row.position.name,
            row.hire_date,
            row.experience_years,
            row.rate_per_shift,
            row.dismissal_date,
        )

    @staticmethod
    def apply(value: Employee, row: EmployeeRow) -> None:
        """Копирует поля, кроме идентификатора и связи с должностью."""
        row.full_name = value.full_name
        row.inn = value.inn
        row.hire_date = value.hire_date
        row.experience_years = value.experience_years
        row.rate_per_shift = value.rate_per_shift
        row.dismissal_date = value.dismissal_date
