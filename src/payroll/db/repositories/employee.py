"""SQL-репозиторий кадровых карточек."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from payroll.db import mappers
from payroll.db.models import EmployeeRow
from payroll.models import Employee
from payroll.repositories.employee import EmployeeRepository


class SqlEmployeeRepository(EmployeeRepository):
    """Хранит карточки в PostgreSQL; идентификатор назначает база."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""

        self._session = session

    def save(self, employee: Employee) -> Employee:
        """Вставляет новую карточку или обновляет существующую по ID."""

        if employee.employee_id:
            row = self._session.get(EmployeeRow, employee.employee_id)
            if row is None:
                raise LookupError(f"сотрудник с ID {employee.employee_id} не найден")
            for field, value in mappers.employee_fields(employee).items():
                setattr(row, field, value)
        else:
            row = EmployeeRow(**mappers.employee_fields(employee))
            self._session.add(row)
        self._session.flush()
        return mappers.employee_to_domain(row)

    def get(self, employee_id: int) -> Employee:
        """Находит сотрудника по идентификатору или сообщает об отсутствии."""

        row = self._session.get(EmployeeRow, employee_id)
        if row is None:
            raise LookupError(f"сотрудник с ID {employee_id} не найден")
        return mappers.employee_to_domain(row)

    def list_all(self) -> list[Employee]:
        """Возвращает все карточки по возрастанию идентификатора."""

        rows = (
            self._session.execute(select(EmployeeRow).order_by(EmployeeRow.employee_id))
            .scalars()
            .all()
        )
        return [mappers.employee_to_domain(row) for row in rows]

    def find_by_inn(self, inn: str) -> Employee | None:
        """Ищет карточку по ИНН; возвращает None, если ИНН свободен."""

        row = self._session.execute(
            select(EmployeeRow).where(EmployeeRow.inn == inn)
        ).scalar_one_or_none()
        return None if row is None else mappers.employee_to_domain(row)

    def count_by_position(self, position: str) -> int:
        """Считает карточки, занимающие должность (для запрета удаления)."""

        return int(
            self._session.execute(
                select(func.count())
                .select_from(EmployeeRow)
                .where(EmployeeRow.position == position)
            ).scalar_one()
        )
