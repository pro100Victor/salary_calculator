"""Контракт и реализации справочника тарифов."""

from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.orm import Session

from salary_calculator.db.mappers.position import PositionMapper
from salary_calculator.db.models import PositionRow
from salary_calculator.models import Position


class PositionRepository(ABC):
    """Находит должности по casefold-ключу, как в исходном сервисе."""

    @abstractmethod
    def get(self, name: str) -> Position:
        """Возвращает должность либо LookupError."""

    @abstractmethod
    def save(self, value: Position) -> None:
        """Сохраняет тариф должности."""

    @abstractmethod
    def list_all(self) -> list[Position]:
        """Возвращает тарифы в порядке добавления."""


class InMemoryPositionRepository(PositionRepository):
    """Хранит тарифы в словаре."""

    def __init__(self) -> None:
        """Создаёт пустой справочник."""
        self._items: dict[str, Position] = {}

    def get(self, name: str) -> Position:
        """Ищет должность без учёта регистра."""
        try:
            return self._items[name.strip().casefold()]
        except KeyError as error:
            raise LookupError(f"должность «{name}» не найдена") from error

    def save(self, value: Position) -> None:
        """Сохраняет должность по нормализованному ключу."""
        self._items[value.name.strip().casefold()] = value

    def list_all(self) -> list[Position]:
        """Возвращает весь справочник."""
        return list(self._items.values())


class SQLAlchemyPositionRepository(PositionRepository):
    """Хранит тарифы через общую Session операции."""

    def __init__(self, session: Session) -> None:
        """Принимает внешнюю Session."""
        self._session = session

    def get_row(self, name: str) -> PositionRow:
        """Находит ORM-запись для внутренней установки FK сотрудника."""
        row = self._session.scalar(
            select(PositionRow).where(
                PositionRow.organization_id == 1,
                PositionRow.name_key == name.strip().casefold(),
            )
        )
        if row is None:
            raise LookupError(f"должность «{name}» не найдена")
        return row

    def get(self, name: str) -> Position:
        """Возвращает независимый от Session тариф."""
        return PositionMapper.to_domain(self.get_row(name))

    def save(self, value: Position) -> None:
        """Обновляет тариф, сохраняя ID и существующие связи."""
        row = self._session.scalar(
            select(PositionRow)
            .where(
                PositionRow.organization_id == 1,
                PositionRow.name_key == value.name.strip().casefold(),
            )
            .with_for_update()
        )
        if row is None:
            row = PositionRow(organization_id=1)
            self._session.add(row)
        PositionMapper.apply(value, row)
        self._session.flush()

    def list_all(self) -> list[Position]:
        """Возвращает должности в порядке ID."""
        rows = self._session.scalars(
            select(PositionRow)
            .where(PositionRow.organization_id == 1)
            .order_by(PositionRow.id)
        )
        return [PositionMapper.to_domain(row) for row in rows]
