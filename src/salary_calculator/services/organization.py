"""Настройки организации и справочник должностей."""

from decimal import ROUND_HALF_UP, Decimal

from salary_calculator.models import Employee, Organization, Position

KOPECK = Decimal("0.01")


class OrganizationService:
    """Хранит реквизиты организации и её собственные тарифы."""

    def __init__(self) -> None:
        """Создаёт пустую конфигурацию предприятия."""

        self._organization: Organization | None = None
        self._positions: dict[str, Position] = {}

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

        self._organization = Organization(name, inn, kpp, address)
        return self._organization

    def get_organization(self) -> Organization:
        """Возвращает настроенное предприятие."""

        if self._organization is None:
            raise LookupError("сначала настройте организацию")
        return self._organization

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
        self._positions[name.casefold()] = position
        return position

    def get_position(self, name: str) -> Position:
        """Находит должность без учёта регистра букв."""

        try:
            return self._positions[name.strip().casefold()]
        except KeyError as error:
            raise LookupError(f"должность «{name}» не найдена") from error

    def list_positions(self) -> list[Position]:
        """Возвращает все доступные должности."""

        return list(self._positions.values())

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
