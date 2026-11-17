"""ORM-модель position."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .organization import OrganizationRow


class PositionRow(Base):
    """Должность: имя для показа и casefold-ключ для уникального поиска."""

    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("organization_id", "name_key"),
        CheckConstraint(
            "length(trim(name)) > 0 AND length(name_key) > 0", name="name_required"
        ),
        CheckConstraint("base_rate > 0 AND base_rate <= 1000000000", name="rate_range"),
        CheckConstraint(
            "seniority_percent >= 0 AND seniority_percent <= 100", name="premium_range"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), default=1
    )
    name: Mapped[str] = mapped_column(Text)
    name_key: Mapped[str] = mapped_column(Text)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    seniority_percent: Mapped[Decimal] = mapped_column(Numeric())
    organization: Mapped[OrganizationRow] = relationship(back_populates="positions")
    employees: Mapped[list[EmployeeRow]] = relationship(
        back_populates="position", passive_deletes="all"
    )
