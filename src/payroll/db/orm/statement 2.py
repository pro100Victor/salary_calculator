"""ORM-модель StatementRow."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Identity,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payroll.db.base import Base

if TYPE_CHECKING:
    from .statement_result import StatementResultRow
    from .timesheet import TimesheetRow


class StatementRow(Base):
    """Шапка расчётной ведомости; название организации — снимок."""

    __tablename__ = "statements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["year", "month"],
            ["timesheets.year", "timesheets.month"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("year", "month", name="uq_statements_year_month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="statements_year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="statements_month_range"),
        CheckConstraint(
            "char_length(trim(organization_name)) BETWEEN 1 AND 255",
            name="statements_organization_name_length",
        ),
        CheckConstraint(
            "source_revision >= 0", name="statements_source_revision_non_negative"
        ),
    )

    statement_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    month: Mapped[int] = mapped_column(SmallInteger)
    organization_name: Mapped[str] = mapped_column(String(255))
    source_revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    timesheet: Mapped["TimesheetRow"] = relationship(back_populates="statement")
    results: Mapped[list["StatementResultRow"]] = relationship(
        back_populates="statement", cascade="all, delete-orphan", passive_deletes=True
    )
