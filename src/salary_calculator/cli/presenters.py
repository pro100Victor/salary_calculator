"""Отдельное форматирование кадров, табеля и расчётных результатов."""

from salary_calculator.models import (
    Employee,
    PayrollResult,
    PayrollStatement,
    Timesheet,
)


def format_employees(employees: list[Employee]) -> str:
    """Выводит карточки сотрудников, включая дату увольнения."""

    if not employees:
        return "список сотрудников пуст"
    return "\n".join(
        f"ID {item.employee_id}: {item.full_name} | {item.position} | "
        f"ИНН {item.inn} | приём {item.hire_date:%d.%m.%Y} | "
        f"стаж {item.experience_years} лет | ставка {item.rate_per_shift:.2f} руб. | "
        f"{item.status}"
        for item in employees
    )


def format_timesheet(timesheet: Timesheet, employees: list[Employee]) -> str:
    """Выводит норму и заполнение каждой строки табеля."""

    by_id = {item.employee_id: item for item in employees}
    lines = [
        f"ТАБЕЛЬ {timesheet.period} | норма: {timesheet.shift_norm} | "
        f"{'закрыт' if timesheet.closed else 'открыт'}"
    ]
    for employee_id in timesheet.employee_ids:
        entry = timesheet.entries.get(employee_id)
        status = (
            "не заполнен"
            if entry is None
            else f"смены {entry.worked_shifts}, болезнь {entry.sick_days}, "
            f"отпуск {entry.vacation_days}; всего {entry.total_days}"
        )
        lines.append(f"ID {employee_id}: {by_id[employee_id].full_name} | {status}")
    return "\n".join(lines)


def format_statement(statement: PayrollStatement, is_current: bool) -> str:
    """Выводит общую ведомость и её итоговую строку."""

    status = "актуальна" if is_current else "устарела: табель изменён"
    lines = [f"ВЕДОМОСТЬ {statement.period} | {statement.organization_name} | {status}"]
    for item in statement.results:
        lines.append(
            f"ID {item.employee.employee_id}: {item.employee.full_name} | "
            f"смен {item.worked_shifts} | начислено {item.accrued:.2f} | "
            f"НДФЛ {item.tax:.2f} | к выплате {item.amount_to_pay:.2f} руб."
        )
    lines.append(
        f"ИТОГО: начислено {statement.total_accrued:.2f} | "
        f"НДФЛ {statement.total_tax:.2f} | "
        f"к выплате {statement.total_to_pay:.2f} руб."
    )
    return "\n".join(lines)


def format_payslip(result: PayrollResult, statement: PayrollStatement) -> str:
    """Выводит листок для просмотра и печати текста терминала."""

    employee = result.employee
    return (
        f"РАСЧЁТНЫЙ ЛИСТОК за {statement.period}\n"
        f"Организация: {statement.organization_name}\n"
        f"Сотрудник: {employee.full_name} (ИНН {employee.inn})\n"
        f"Должность: {employee.position}\n"
        f"Ставка за смену: {employee.rate_per_shift:.2f} руб.\n"
        f"Отработано смен: {result.worked_shifts}\n"
        f"Больничный: {result.sick_days} дн. | Отпуск: {result.vacation_days} дн.\n"
        f"Начислено: {result.accrued:.2f} руб.\n"
        f"НДФЛ 13%: {result.tax:.2f} руб.\n"
        f"К ВЫПЛАТЕ: {result.amount_to_pay:.2f} руб."
    )
