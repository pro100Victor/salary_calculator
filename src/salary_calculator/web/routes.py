"""Команды экранов: ввод → сервис → JSON, без формул и SQL."""

from typing import Any

from fastapi import APIRouter, Depends, Request

from salary_calculator.models import Period
from salary_calculator.web.dependencies import Services, require_login
from salary_calculator.web.schemas.calculation import CalculationInput
from salary_calculator.web.schemas.dismissal import DismissalInput
from salary_calculator.web.schemas.employee import EmployeeInput
from salary_calculator.web.schemas.entry import EntryInput
from salary_calculator.web.schemas.norm import NormInput
from salary_calculator.web.schemas.organization import OrganizationInput
from salary_calculator.web.schemas.position import PositionInput
from salary_calculator.web.serialization import to_json
from salary_calculator.web.validation import checked
from salary_calculator.web.views import directory_view, period_view

router = APIRouter(prefix="/api", dependencies=[Depends(require_login)])


def read_period(year: int, month: int) -> Period:
    """Передаёт год и месяц валидаторам модели с именами полей формы."""

    checked("year", lambda: Period.validate_year(year))
    checked("month", lambda: Period.validate_month(month))
    return Period(year, month)


@router.get("/state")
def state(services: Services, request: Request) -> dict[str, Any]:
    """Возвращает справочники и режим хранения для главной страницы."""

    return {
        **directory_view(services),
        "storage_mode": request.app.state.provider.storage_mode,
    }


@router.put("/organization")
def organization(data: OrganizationInput, services: Services) -> Any:
    """Сохраняет реквизиты с общими для CLI и веба правилами."""

    service = services.organization
    checked("name", lambda: service.validate_name(data.name))
    checked("inn", lambda: service.validate_inn(data.inn))
    checked("kpp", lambda: service.validate_kpp(data.kpp, data.inn))
    checked("address", lambda: service.validate_address(data.address))
    return to_json(service.set_organization(**data.model_dump()))


@router.put("/positions")
def position(data: PositionInput, services: Services) -> Any:
    """Добавляет или обновляет тариф существующим сервисом организации."""

    service = services.organization
    service.get_organization()
    checked("name", lambda: service.validate_position_name(data.name))
    checked("base_rate", lambda: service.validate_base_rate(data.base_rate))
    checked(
        "seniority_percent",
        lambda: service.validate_seniority_percent(data.seniority_percent),
    )
    return to_json(service.set_position(**data.model_dump()))


@router.get("/rate")
def rate(position: str, experience_years: int, services: Services) -> dict[str, str]:
    """Показывает ставку с сервера без повторения формулы в JavaScript."""

    checked("position", lambda: services.organization.get_position(position))
    checked(
        "experience_years",
        lambda: services.organization.validate_experience_years(experience_years),
    )
    return {
        "rate_per_shift": str(
            services.organization.rate_for(position, experience_years)
        )
    }


def validate_employee(
    data: EmployeeInput, services: Services, employee_id: int | None = None
) -> None:
    """Связывает поля формы с публичными валидаторами сервисов и моделей."""

    service = services.employees
    old = service.get_employee_by_id(employee_id) if employee_id is not None else None
    checked("full_name", lambda: service.validate_full_name(data.full_name))
    checked(
        "inn", lambda: service.validate_inn(data.inn.strip(), except_id=employee_id)
    )
    checked("position", lambda: services.organization.get_position(data.position))
    checked(
        "hire_date",
        lambda: service.validate_hire_date(
            data.hire_date, old.dismissal_date if old else None
        ),
    )
    checked(
        "experience_years",
        lambda: services.organization.validate_experience_years(data.experience_years),
    )


@router.post("/employees", status_code=201)
def add_employee(data: EmployeeInput, services: Services) -> Any:
    """Создаёт карточку; окончательная проверка остаётся в сервисе."""

    services.organization.get_organization()
    validate_employee(data, services)
    return to_json(services.employees.add_employee(**data.model_dump()))


@router.put("/employees/{employee_id}")
def update_employee(employee_id: int, data: EmployeeInput, services: Services) -> Any:
    """Редактирует карточку с сохранением серверного расчёта ставки."""

    validate_employee(data, services, employee_id)
    return to_json(services.employees.update_employee(employee_id, **data.model_dump()))


@router.post("/employees/{employee_id}/dismiss")
def dismiss_employee(employee_id: int, data: DismissalInput, services: Services) -> Any:
    """Увольняет сотрудника, не удаляя его историю."""

    checked(
        "dismissal_date",
        lambda: services.employees.validate_dismissal_date(
            employee_id, data.dismissal_date
        ),
    )
    return to_json(
        services.employees.dismiss_employee(employee_id, data.dismissal_date)
    )


@router.get("/periods/{year}/{month}")
def get_period(year: int, month: int, services: Services) -> dict[str, Any]:
    """Загружает выбранный период без создания данных."""

    return period_view(services, read_period(year, month))


@router.put("/periods/{year}/{month}/norm")
def norm(year: int, month: int, data: NormInput, services: Services) -> dict[str, Any]:
    """Меняет норму только до создания табеля, как в существующем CLI."""

    period = read_period(year, month)
    try:
        services.timesheets.get(period)
    except LookupError:
        pass
    else:
        raise ValueError("табель уже создан; норма периода зафиксирована")
    checked("shifts", lambda: services.calendar.validate_norm(period, data.shifts))
    services.calendar.set_norm(period, data.shifts)
    return period_view(services, period)


@router.post("/periods/{year}/{month}/timesheet")
def generate(year: int, month: int, services: Services) -> dict[str, Any]:
    """Формирует табель по пересечению месяца с датами работы сотрудников."""

    period = read_period(year, month)
    services.organization.get_organization()
    services.timesheets.generate(period)
    return period_view(services, period)


@router.put("/periods/{year}/{month}/entries/{employee_id}")
def fill(
    year: int, month: int, employee_id: int, data: EntryInput, services: Services
) -> dict[str, Any]:
    """Сохраняет одну строку; при ошибке остальные строки не меняются."""

    period = read_period(year, month)
    sheet = services.timesheets.get(period)
    if sheet.closed:
        raise ValueError("расчётный период закрыт")
    checked("worked_shifts", lambda: sheet.validate_days(data.worked_shifts))
    checked(
        "sick_days", lambda: sheet.validate_days(data.sick_days, data.worked_shifts)
    )
    checked(
        "vacation_days",
        lambda: sheet.validate_days(
            data.vacation_days, data.worked_shifts + data.sick_days
        ),
    )
    services.timesheets.fill(period, employee_id, **data.model_dump())
    return period_view(services, period)


@router.post("/periods/{year}/{month}/statement")
def calculate(
    year: int, month: int, data: CalculationInput, services: Services
) -> dict[str, Any]:
    """Запускает существующее расчётное ядро с явным подтверждением перерасчёта."""

    period = read_period(year, month)
    services.payroll.calculate_period(period, data.replace_existing)
    return period_view(services, period)


@router.post("/periods/{year}/{month}/close")
def close(year: int, month: int, services: Services) -> dict[str, Any]:
    """Закрывает период через проверку актуальности ведомости в PayrollService."""

    period = read_period(year, month)
    services.payroll.close_period(period)
    return period_view(services, period)
