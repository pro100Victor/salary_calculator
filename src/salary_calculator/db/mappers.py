"""Совместимый API мапперов; реализации находятся в db/mapping/."""

from salary_calculator.db.mapping.employee import EmployeeMapper
from salary_calculator.db.mapping.organization import OrganizationMapper
from salary_calculator.db.mapping.payroll_result import PayrollResultMapper
from salary_calculator.db.mapping.position import PositionMapper
from salary_calculator.db.mapping.statement import StatementMapper
from salary_calculator.db.mapping.timesheet import TimesheetMapper

organization_to_domain = OrganizationMapper.to_domain
apply_organization = OrganizationMapper.apply
position_to_domain = PositionMapper.to_domain
employee_to_domain = EmployeeMapper.to_domain
employee_fields = EmployeeMapper.fields
timesheet_to_domain = TimesheetMapper.to_domain
statement_to_domain = StatementMapper.to_domain
result_fields = PayrollResultMapper.fields
