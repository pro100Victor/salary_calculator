"""Преобразование organization без SQL-запросов и управления Session."""

from salary_calculator.db.models import OrganizationRow
from salary_calculator.models import Organization


class OrganizationMapper:
    """Преобразует таблицу organization и предметный объект."""

    @staticmethod
    def to_domain(row: OrganizationRow) -> Organization:
        """Создаёт проверенный dataclass из загруженной записи."""
        return Organization(row.name, row.inn, row.kpp, row.address)

    @staticmethod
    def apply(value: Organization, row: OrganizationRow) -> None:
        """Копирует предметные поля в существующую ORM-запись."""
        row.name = value.name
        row.inn = value.inn
        row.kpp = value.kpp
        row.address = value.address
