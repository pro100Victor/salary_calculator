"""Настройки организации и справочник должностей."""

from decimal import ROUND_HALF_UP, Decimal

from salary_calculator.models import Employee, Organization, Position
from salary_calculator.repositories.organization import (
    InMemoryOrganizationRepository,
    OrganizationRepository,
)
from salary_calculator.repositories.position import (
    InMemoryPositionRepository,
    PositionRepository,
)

KOPECK = Decimal("0.01")


class OrganizationService:
    """Хранит реквизиты организации и её собственные тарифы."""

    def __init__(
        self,
        repository: OrganizationRepository | None = None,
        positions: PositionRepository | None = None,
    ) -> None:
        """Создаёт пустую конфигурацию предприятия."""

        self._repository = (
            repository if repository is not None else InMemoryOrganizationRepository()
        )
        self._positions = (
            positions if positions is not None else InMemoryPositionRepository()
        )

    @staticmethod
    def validate_name(value: str) -> str:
        """Проверяет название организации."""
        return Organization.validate_name(value)

    @staticmethod
    def validate_inn(value: str) -> str:
        """Проверяет формат ИНН организации."""
        return Organization.validate_inn(value)

    @staticmethod
    def validate_kpp(value: str, inn: str) -> str:
        """Проверяет КПП с учётом ИНН организации."""
        return Organization.validate_kpp(value, inn)

    @staticmethod
    def validate_address(value: str) -> str:
        """Проверяет адрес организации."""
        return Organization.validate_address(value)

    def set_organization(
        self, name: str, inn: str, kpp: str, address: str
    ) -> Organization:
        """Проверяет и сохраняет сведения о предприятии."""
        name = self.validate_name(name)
        inn = self.validate_inn(inn)
        kpp = self.validate_kpp(kpp, inn)
        address = self.validate_address(address)

        return self._repository.save(Organization(name, inn, kpp, address))

    def get_organization(self) -> Organization:
        """Возвращает настроенное предприятие."""

        return self._repository.get()

    def set_position(
        self,
        name: str,
        base_rate: Decimal | str | float,
        seniority_percent: Decimal | str | float = 0,
    ) -> Position:
        """Добавляет или обновляет должность с тарифом за смену."""

        name = self.validate_position_name(name)
        rate = self.validate_base_rate(base_rate)
        percent = self.validate_seniority_percent(seniority_percent)

        position = Position(name, rate, percent)
        try:
            existing = self.get_position(name)
        except LookupError:
            return self._positions.save(position)
        return self._positions.save(Position(existing.name, rate, percent))

    def get_position(self, name: str) -> Position:
        """Находит должность без учёта регистра букв."""

        key = name.strip().casefold()
        for position in self._positions.list_all():
            if position.name.casefold() == key:
                return position
        raise LookupError(f"должность «{name}» не найдена")

    def list_positions(self) -> list[Position]:
        """Возвращает все доступные должности."""

        return self._positions.list_all()

    def rate_for(self, name: str, experience_years: int) -> Decimal:
        """Рассчитывает ставку по должности и полным годам стажа."""

        self.validate_experience_years(experience_years)

        position = self.get_position(name)
        multiplier = Decimal(1) + (
            position.seniority_percent * experience_years / Decimal(100)
        )
        return (position.base_rate * multiplier).quantize(
            KOPECK, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def validate_position_name(value: str) -> str:
        """Проверяет название должности."""
        return Position.validate_position_name(value)

    @staticmethod
    def validate_base_rate(value: Decimal | str | float) -> Decimal:
        """Проверяет базовую ставку."""
        return Position.validate_base_rate(value)

    @staticmethod
    def validate_seniority_percent(value: Decimal | str | float) -> Decimal:
        """Проверяет надбавку за стаж."""
        return Position.validate_seniority_percent(value)

    @staticmethod
    def validate_experience_years(value: int) -> None:
        Employee.validate_experience_years(value)
