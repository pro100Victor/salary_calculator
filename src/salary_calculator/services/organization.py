"""Настройки организации и справочник должностей."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from salary_calculator.models import Organization, Position

KOPECK = Decimal("0.01")


def as_decimal(value: Decimal | str | float) -> Decimal:
    """Преобразует число в конечный Decimal без двоичной ошибки float."""

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("введите корректную денежную сумму") from error

    if not number.is_finite():
        raise ValueError("денежная сумма должна быть конечной")

    return number


class OrganizationService:
    """Хранит реквизиты организации и её собственные тарифы."""

    def __init__(self) -> None:
        """Создаёт пустую конфигурацию предприятия."""

        self._organization: Organization | None = None
        self._positions: dict[str, Position] = {}

    @staticmethod
    def validate_name(value: str) -> str:
        """Проверяет название организации."""
        name = value.strip()
        if not name:
            raise ValueError("название организации не должно быть пустым")
        return name

    @staticmethod
    def validate_inn(value: str) -> str:
        """Проверяет формат ИНН организации."""
        inn = value.strip()
        if len(inn) not in (10, 12) or not inn.isascii() or not inn.isdigit():
            raise ValueError("ИНН организации должен содержать 10 или 12 цифр")
        return inn

    @staticmethod
    def validate_kpp(value: str, inn: str) -> str:
        """Проверяет КПП с учётом ИНН организации."""
        kpp = value.strip()
        if kpp and (len(kpp) != 9 or not kpp.isascii() or not kpp.isdigit()):
            raise ValueError("КПП должен содержать 9 цифр или быть пустым для ИП")
        if len(inn.strip()) == 12 and kpp:
            raise ValueError("для ИП с 12-значным ИНН КПП оставляют пустым")
        return kpp

    @staticmethod
    def validate_address(value: str) -> str:
        """Проверяет адрес организации."""
        address = value.strip()
        if not address:
            raise ValueError("адрес организации не должен быть пустым")
        return address

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
        name = value.strip()
        if not name:
            raise ValueError("название должности не может быть пустым")
        return name

    @staticmethod
    def validate_base_rate(value: Decimal | str | float) -> Decimal:
        """Проверяет базовую ставку."""
        rate = as_decimal(value)
        if rate > Decimal(1000000000):
            raise ValueError("ставка за смену слишком велика")
        if rate <= 0 or rate != rate.quantize(KOPECK):
            raise ValueError("ставка должна быть положительной суммой с двумя знаками")
        return rate

    @staticmethod
    def validate_seniority_percent(value: Decimal | str | float) -> Decimal:
        """Проверяет надбавку за стаж."""
        percent = as_decimal(value)
        if not 0 <= percent <= 100:
            raise ValueError("надбавка за год стажа должна быть от 0 до 100%")
        return percent

    @staticmethod
    def validate_experience_years(value: int) -> None:
        """Проверяет стаж в полных годах."""
        if type(value) is not int or not 0 <= value <= 80:
            raise ValueError("стаж должен быть целым числом от 0 до 80 лет")
