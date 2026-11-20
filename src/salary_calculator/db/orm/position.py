"""ORM-модель PositionRow."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow


class PositionRow(Base):
    """Должность с базовой ставкой и надбавкой за полный год стажа."""

    __tablename__ = "positions"
    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) BETWEEN 1 AND 120", name="positions_name_length"
        ),
        CheckConstraint("base_rate > 0", name="positions_base_rate_positive"),
        CheckConstraint(
            "seniority_percent BETWEEN 0 AND 100",
            name="positions_seniority_percent_range",
        ),
    )

    name: Mapped[str] = mapped_column(String(120), primary_key=True)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    seniority_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    employees: Mapped[list["EmployeeRow"]] = relationship(
        back_populates="position_row", passive_deletes="all"
    )
