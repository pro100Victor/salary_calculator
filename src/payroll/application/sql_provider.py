"""SQL-сборка сервисов: Session на операцию и честная транзакция."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from payroll.application.errors import StorageError
from payroll.application.provider import ServiceProvider
from payroll.application.services import ApplicationServices
from payroll.db.repositories.calendar_norm import SqlCalendarNormRepository
from payroll.db.repositories.employee import SqlEmployeeRepository
from payroll.db.repositories.organization import SqlOrganizationRepository
from payroll.db.repositories.position import SqlPositionRepository
from payroll.db.repositories.statement import SqlStatementRepository
from payroll.db.repositories.timesheet import SqlTimesheetRepository
from payroll.services.calendar import CalendarService
from payroll.services.employee import EmployeeService
from payroll.services.organization import OrganizationService
from payroll.services.payroll import PayrollService
from payroll.services.timesheet import TimesheetService


class SQLServiceProvider(ServiceProvider):
    """Создаёт сервисы на одну операцию поверх Session PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        """Строит пул соединений; URL не раскрывается интерфейсу."""

        self.engine = create_engine(database_url, pool_pre_ping=True)
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @property
    def storage_mode(self) -> str:
        """Показывает интерфейсу, что данные теперь долговременны."""

        return "PostgreSQL — данные в базе данных"

    @contextmanager
    def operation(self) -> Iterator[ApplicationServices]:
        """Открывает транзакцию: успех коммитится, ошибка откатывается."""

        session: Session = self._sessions()
        try:
            organization = OrganizationService(
                SqlOrganizationRepository(session), SqlPositionRepository(session)
            )
            employees = EmployeeService(SqlEmployeeRepository(session), organization)
            calendar = CalendarService(SqlCalendarNormRepository(session))
            timesheets = TimesheetService(
                SqlTimesheetRepository(session), employees, calendar
            )
            payroll = PayrollService(
                SqlStatementRepository(session), timesheets, employees, organization
            )
            yield ApplicationServices(
                organization, employees, calendar, timesheets, payroll
            )
            session.commit()
        except IntegrityError as error:
            session.rollback()
            constraint = getattr(
                getattr(error.orig, "diag", None), "constraint_name", ""
            )
            if constraint == "uq_employees_inn":
                raise ValueError("сотрудник с таким ИНН уже существует") from None
            raise ValueError(
                "данные нарушают ограничения базы; операция отменена"
            ) from None
        except SQLAlchemyError:
            session.rollback()
            raise StorageError(
                "хранилище данных недоступно; операция отменена"
            ) from None
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()
