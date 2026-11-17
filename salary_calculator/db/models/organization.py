"""ORM-модель organization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base
from salary_calculator.db.checks import digits_only

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .period import PeriodRow
    from .position import PositionRow


class OrganizationRow(Base):
    """Реквизиты единственной настраиваемой организации установки."""

    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_organization"),
        CheckConstraint("length(trim(name)) > 0", name="name_required"),
        CheckConstraint("length(trim(address)) > 0", name="address_required"),
        CheckConstraint(
            "length(inn) IN (10, 12) AND " + digits_only("inn"), name="inn_format"
        ),
        CheckConstraint(
            "kpp = '' OR (length(kpp) = 9 AND " + digits_only("kpp") + ")",
            name="kpp_format",
        ),
        CheckConstraint("length(inn) != 12 OR kpp = ''", name="individual_kpp"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(Text)
    inn: Mapped[str] = mapped_column(Text, unique=True)
    kpp: Mapped[str] = mapped_column(Text)
    address: Mapped[str] = mapped_column(Text)
    positions: Mapped[list[PositionRow]] = relationship(
        back_populates="organization", passive_deletes="all"
    )
    employees: Mapped[list[EmployeeRow]] = relationship(
        back_populates="organization", passive_deletes="all"
    )
    periods: Mapped[list[PeriodRow]] = relationship(
        back_populates="organization", passive_deletes="all"
    )
