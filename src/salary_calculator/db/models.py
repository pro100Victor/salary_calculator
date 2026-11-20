"""Совместимые импорты ORM-моделей; определения находятся в db/orm/."""

from salary_calculator.db.base import Base as Base
from salary_calculator.db.orm.calendar_norm import CalendarNormRow as CalendarNormRow
from salary_calculator.db.orm.employee import EmployeeRow as EmployeeRow
from salary_calculator.db.orm.organization import OrganizationRow as OrganizationRow
from salary_calculator.db.orm.position import PositionRow as PositionRow
from salary_calculator.db.orm.statement import StatementRow as StatementRow
from salary_calculator.db.orm.statement_result import (
    StatementResultRow as StatementResultRow,
)
from salary_calculator.db.orm.timesheet import TimesheetRow as TimesheetRow
from salary_calculator.db.orm.timesheet_entry import (
    TimesheetEntryRow as TimesheetEntryRow,
)
