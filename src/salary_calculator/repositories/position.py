"""Контракт хранения должностей и тарифов."""

from abc import ABC, abstractmethod

from salary_calculator.models import Position


class PositionRepository(ABC):
    """Определяет обязательные операции хранилища должностей."""

    @abstractmethod
    def save(self, position: Position) -> Position:
        """Создаёт должность или обновляет тариф по имени."""

    @abstractmethod
    def get(self, name: str) -> Position:
        """Находит должность по имени; при отсутствии — LookupError."""

    @abstractmethod
    def list_all(self) -> list[Position]:
        """Возвращает все должности."""


class InMemoryPositionRepository(PositionRepository):
    """Хранит должности в словаре по имени."""

    def __init__(self) -> None:
        """Создаёт пустой справочник должностей."""

        self._items: dict[str, Position] = {}

    def save(self, position: Position) -> Position:
        """Добавляет или обновляет должность."""

        self._items[position.name.casefold()] = position
        return position

    def get(self, name: str) -> Position:
        """Находит должность по имени."""

        try:
            return self._items[name.strip().casefold()]
        except KeyError as error:
            raise LookupError(f"должность {name} не найдена") from error

    def list_all(self) -> list[Position]:
        """Возвращает все должности."""

        return list(self._items.values())
