"""Совместимые импорты ORM-моделей; определения находятся в db/orm/."""

from payroll.db.base import Base as Base
from payroll.db.orm.calendar_norm import CalendarNormRow as CalendarNormRow
from payroll.db.orm.employee import EmployeeRow as EmployeeRow
from payroll.db.orm.organization import OrganizationRow as OrganizationRow
from payroll.db.orm.position import PositionRow as PositionRow
from payroll.db.orm.statement import StatementRow as StatementRow
from payroll.db.orm.statement_result import (
    StatementResultRow as StatementResultRow,
)
from payroll.db.orm.timesheet import TimesheetRow as TimesheetRow
from payroll.db.orm.timesheet_entry import (
    TimesheetEntryRow as TimesheetEntryRow,
)
