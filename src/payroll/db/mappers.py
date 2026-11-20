"""Совместимый API мапперов; реализации находятся в db/mapping/."""

from payroll.db.mapping.employee import EmployeeMapper
from payroll.db.mapping.organization import OrganizationMapper
from payroll.db.mapping.payroll_result import PayrollResultMapper
from payroll.db.mapping.position import PositionMapper
from payroll.db.mapping.statement import StatementMapper
from payroll.db.mapping.timesheet import TimesheetMapper

organization_to_domain = OrganizationMapper.to_domain
apply_organization = OrganizationMapper.apply
position_to_domain = PositionMapper.to_domain
employee_to_domain = EmployeeMapper.to_domain
employee_fields = EmployeeMapper.fields
timesheet_to_domain = TimesheetMapper.to_domain
statement_to_domain = StatementMapper.to_domain
result_fields = PayrollResultMapper.fields
