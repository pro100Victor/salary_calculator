from dataclasses import dataclass


@dataclass(frozen=True)
class Organization:
    """Содержит реквизиты малого предприятия."""

    name: str
    inn: str
    kpp: str
    address: str

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

    def __post_init__(self) -> None:
        """Проверяет реквизиты при создании организации."""
        self.validate_name(self.name)
        self.validate_inn(self.inn)
        self.validate_kpp(self.kpp, self.inn)
        self.validate_address(self.address)
