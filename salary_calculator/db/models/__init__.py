"""Импорт всех таблиц для настройки relationships и метаданных Alembic."""

from .employee import EmployeeRow as EmployeeRow
from .organization import OrganizationRow as OrganizationRow
from .payroll_result import PayrollResultRow as PayrollResultRow
from .payroll_statement import PayrollStatementRow as PayrollStatementRow
from .period import PeriodRow as PeriodRow
from .position import PositionRow as PositionRow
from .timesheet import TimesheetRow as TimesheetRow
from .timesheet_entry import TimesheetEntryRow as TimesheetEntryRow
