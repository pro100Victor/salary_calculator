from dataclasses import dataclass


@dataclass(frozen=True)
class Organization:
    """Содержит реквизиты малого предприятия."""

    name: str
    inn: str
    kpp: str
    address: str