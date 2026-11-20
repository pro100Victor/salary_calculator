"""Маппер OrganizationMapper."""

from salary_calculator.db.models import (
    OrganizationRow,
)
from salary_calculator.models import (
    Organization,
)


class OrganizationMapper:
    """Преобразует ORM-данные в предметные модели без открытой Session."""

    @staticmethod
    def to_domain(row: OrganizationRow) -> Organization:
        """Собирает доменную модель реквизитов из ORM-ряда."""

        return Organization(row.name, row.inn, row.kpp or "", row.address)

    @staticmethod
    def apply(row: OrganizationRow, organization: Organization) -> None:
        """Переносит доменные реквизиты в ORM-ряд (КПП-пустота это NULL)."""

        row.name = organization.name
        row.inn = organization.inn
        row.kpp = organization.kpp or None
        row.address = organization.address
