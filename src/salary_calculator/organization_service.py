"""Настройки организации и справочник должностей."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from salary_calculator.models import Organization, Position

KOPECK = Decimal("0.01")


def as_decimal(value: Decimal | str | int | float) -> Decimal:
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

    def set_organization(
        self, name: str, inn: str, kpp: str, address: str
    ) -> Organization:
        """Проверяет и сохраняет сведения о предприятии."""

        name, inn, kpp, address = (
            name.strip(),
            inn.strip(),
            kpp.strip(),
            address.strip(),
        )
        if not name or not address:
            raise ValueError("название и адрес организации обязательны")
        if len(inn) not in (10, 12) or not inn.isascii() or not inn.isdigit():
            raise ValueError("ИНН организации должен содержать 10 или 12 цифр")
        if kpp and (len(kpp) != 9 or not kpp.isascii() or not kpp.isdigit()):
            raise ValueError("КПП должен содержать 9 цифр или быть пустым для ИП")
        if len(inn) == 12 and kpp:
            raise ValueError("для ИП с 12-значным ИНН КПП оставляют пустым")

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
        base_rate: Decimal | str | int | float,
        seniority_percent: Decimal | str | int | float = 0,
    ) -> Position:
        """Добавляет или обновляет должность с тарифом за смену."""

        name = name.strip()
        rate = as_decimal(base_rate)
        percent = as_decimal(seniority_percent)
        if not name:
            raise ValueError("название должности не может быть пустым")
        if rate > Decimal("1000000000"):
            raise ValueError("ставка за смену слишком велика")
        if rate <= 0 or rate != rate.quantize(KOPECK):
            raise ValueError("ставка должна быть положительной суммой с двумя знаками")
        if percent < 0 or percent > 100:
            raise ValueError("надбавка за год стажа должна быть от 0 до 100%")

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

        if (
            isinstance(experience_years, bool)
            or not isinstance(experience_years, int)
            or not 0 <= experience_years <= 80
        ):
            raise ValueError("стаж должен быть целым числом от 0 до 80 лет")

        position = self.get_position(name)
        multiplier = Decimal("1") + (
            position.seniority_percent * experience_years / Decimal("100")
        )
        return (position.base_rate * multiplier).quantize(
            KOPECK, rounding=ROUND_HALF_UP
        )
