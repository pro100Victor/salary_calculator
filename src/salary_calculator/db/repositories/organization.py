"""SQL-репозиторий реквизитов предприятия (одна строка с id = 1)."""

from sqlalchemy.orm import Session

from salary_calculator.db import mappers
from salary_calculator.db.models import OrganizationRow
from salary_calculator.models import Organization
from salary_calculator.repositories.organization import OrganizationRepository


class SqlOrganizationRepository(OrganizationRepository):
    """Хранит единственные реквизиты предприятия."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""

        self._session = session

    def get(self) -> Organization:
        """Возвращает реквизиты или требует первоначальной настройки."""

        row = self._session.get(OrganizationRow, 1)
        if row is None:
            raise LookupError("сначала настройте организацию")
        return mappers.organization_to_domain(row)

    def save(self, organization: Organization) -> Organization:
        """Создаёт или обновляет единственную строку реквизитов."""

        row = self._session.get(OrganizationRow, 1)
        if row is None:
            row = OrganizationRow(id=1)
            self._session.add(row)
        mappers.apply_organization(row, organization)
        self._session.flush()
        return organization
