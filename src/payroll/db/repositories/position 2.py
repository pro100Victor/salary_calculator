"""SQL-репозиторий должностей с обновлением тарифа по имени."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from payroll.db import mappers
from payroll.db.models import PositionRow
from payroll.models import Position
from payroll.repositories.position import PositionRepository


class SqlPositionRepository(PositionRepository):
    """Сохраняет должности; повторное имя обновляет тариф."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""

        self._session = session

    def save(self, position: Position) -> Position:
        """Вставляет новую должность или обновляет ставки существующей."""

        row = self._session.get(PositionRow, position.name)
        if row is None:
            self._session.add(
                PositionRow(
                    name=position.name,
                    base_rate=position.base_rate,
                    seniority_percent=position.seniority_percent,
                )
            )
        else:
            row.base_rate = position.base_rate
            row.seniority_percent = position.seniority_percent
        self._session.flush()
        return position

    def get(self, name: str) -> Position:
        """Находит должность по имени или сообщает о её отсутствии."""

        row = self._session.get(PositionRow, name)
        if row is None:
            raise LookupError(f"должность {name} не найдена")
        return mappers.position_to_domain(row)

    def list_all(self) -> list[Position]:
        """Возвращает все должности по алфавиту."""

        rows = (
            self._session.execute(select(PositionRow).order_by(PositionRow.name))
            .scalars()
            .all()
        )
        return [mappers.position_to_domain(row) for row in rows]
