"""Транзакционная блокировка периода, включая ещё не созданный табель."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from payroll.models import Period


def lock_period(session: Session, period: Period) -> None:
    """Упорядочивает операции нормы, табеля и ведомости одного месяца."""

    if session.get_bind().dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(:namespace, :period)"),
            {"namespace": 814, "period": period.year * 12 + period.month},
        )
