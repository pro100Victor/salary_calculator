"""ORM-модель OrganizationRow."""

from sqlalchemy import (
    CheckConstraint,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from payroll.db.base import Base


class OrganizationRow(Base):
    """Реквизиты предприятия; в таблице всегда одна строка с id = 1."""

    __tablename__ = "organization"
    __table_args__ = (
        CheckConstraint("id = 1", name="organization_singleton"),
        CheckConstraint(
            "char_length(inn) <> 12 OR kpp IS NULL", name="organization_ip_kpp"
        ),
        CheckConstraint(
            "char_length(trim(name)) BETWEEN 1 AND 255", name="organization_name_length"
        ),
        CheckConstraint(
            "inn ~ '^[0-9]{10}$' OR inn ~ '^[0-9]{12}$'", name="organization_inn_format"
        ),
        CheckConstraint(
            "kpp IS NULL OR kpp ~ '^[0-9]{9}$'", name="organization_kpp_format"
        ),
        CheckConstraint(
            "char_length(trim(address)) BETWEEN 1 AND 255",
            name="organization_address_length",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str] = mapped_column(String(12))
    kpp: Mapped[str | None] = mapped_column(String(9))
    address: Mapped[str] = mapped_column(String(255))
