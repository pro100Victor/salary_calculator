"""Тестовая реализация провайдера; промышленную сборку делает инженер 3."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from salary_calculator.application.errors import StorageError
from salary_calculator.application.provider import ServiceProvider
from salary_calculator.application.services import ApplicationServices
from salary_calculator.application.sql_services import build_sql_services


class TestSQLProvider(ServiceProvider):
    """Открывает одну Session и транзакцию на вызов для проверки контрактов."""

    __test__ = False

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        """Получает фабрику тестовых сессий."""
        self.sessions = sessions

    @property
    def storage_mode(self) -> str:
        """Явно сообщает тестовое хранилище."""
        return "SQLAlchemy / SQLite — интеграционный тест"

    @contextmanager
    def operation(self) -> Iterator[ApplicationServices]:
        """Откатывает исключение до передачи ошибки интерфейсу."""
        try:
            with self.sessions() as session, session.begin():
                yield build_sql_services(session)
        except IntegrityError as error:
            raise ValueError("конфликт ограничения БД") from error
        except SQLAlchemyError as error:
            raise StorageError("сбой тестовой БД") from error
