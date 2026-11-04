"""Пользовательские сценарии CLI для всех функций учебного прототипа."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal

from salary_calculator.auth_service import AuthService
from salary_calculator.calendar_service import CalendarService
from salary_calculator.cli.input_helpers import InputReader
from salary_calculator.cli.presenters import (
    format_employees,
    format_payslip,
    format_statement,
    format_timesheet,
)
from salary_calculator.employee_service import EmployeeService
from salary_calculator.models import Period
from salary_calculator.organization_service import OrganizationService
from salary_calculator.payroll_service import PayrollService
from salary_calculator.timesheet_service import TimesheetService


class SalaryCalculatorCLI:
    """Связывает команды бухгалтера с сервисами без расчётных формул в меню."""

    def __init__(
        self,
        auth: AuthService,
        organization: OrganizationService,
        employees: EmployeeService,
        calendar: CalendarService,
        timesheets: TimesheetService,
        payroll: PayrollService,
        reader: InputReader | None = None,
        output: Callable[[str], None] | None = None,
    ) -> None:
        """Принимает подготовленные сервисы и функции ввода-вывода."""

        self._auth = auth
        self._organization = organization
        self._employees = employees
        self._calendar = calendar
        self._timesheets = timesheets
        self._payroll = payroll
        self._output = output or print
        self._reader = reader or InputReader(output_function=self._output)
        self._running = True

    def run(self) -> None:
        """Авторизует бухгалтера и обрабатывает команды до завершения."""

        actions: dict[int, Callable[[], None]] = {
            1: self._configure_organization,
            2: self._configure_position,
            3: self._add_employee,
            4: self._edit_employee,
            5: self._dismiss_employee,
            6: self._show_employees,
            7: self._set_calendar_norm,
            8: self._open_timesheet,
            9: self._fill_timesheet,
            10: self._calculate_statement,
            11: self._show_statement,
            12: self._show_payslip,
            13: self._close_period,
            0: self._stop,
        }

        self._output("Salary Calculator — лабораторная работа №3")
        self._output("Учебная учётная запись: admin / admin")
        try:
            if not self._login():
                return
            while self._running:
                self._show_menu()
                try:
                    choice = self._reader.read_int("выберите действие: ", 0, 13)
                    self._auth.require_login()
                    actions[choice]()
                except (ValueError, LookupError, PermissionError) as error:
                    self._output(f"ошибка: {error}")
        except (EOFError, KeyboardInterrupt):
            self._output("\nработа программы завершена")
        finally:
            self._auth.logout()

    def _existing_period(self, lookup: Callable[[Period], object]) -> Period:
        """Повторяет выбор периода, пока нужные данные не будут найдены."""

        return self._reader.read_checked(self._period, lookup)

    def _login(self) -> bool:
        """Предоставляет три попытки входа в учебную систему."""

        for attempt in range(3):
            username = self._reader.read_non_empty("логин: ")
            password = self._reader.read_non_empty("пароль: ")
            if self._auth.login(username, password):
                self._output("вход выполнен")
                return True
            self._output(f"неверный логин или пароль; осталось попыток: {2 - attempt}")
        return False

    def _show_menu(self) -> None:
        """Выводит пункты пользовательского меню."""

        self._output(
            "\n1 — настроить организацию\n"
            "2 — добавить или изменить должность и тариф\n"
            "3 — добавить сотрудника\n"
            "4 — изменить сотрудника\n"
            "5 — уволить сотрудника\n"
            "6 — список сотрудников\n"
            "7 — задать норму смен на месяц\n"
            "8 — сформировать или открыть табель\n"
            "9 — заполнить строку табеля\n"
            "10 — рассчитать зарплату за месяц\n"
            "11 — просмотреть расчётную ведомость\n"
            "12 — просмотреть расчётный листок\n"
            "13 — закрыть расчётный период\n"
            "0 — выход"
        )

    def _period(self) -> Period:
        """Запрашивает расчётный месяц и год."""

        year = self._reader.read_int("год: ", 1, 9999)
        month = self._reader.read_int("месяц (1–12): ", 1, 12)
        return Period(year, month)

    def _read_inn(self, employee_id: int | None = None) -> str:
        """Запрашивает ИНН до прохождения проверки формата и уникальности."""

        return self._reader.read_checked(
            lambda: self._reader.read_non_empty("ИНН сотрудника (12 цифр): "),
            lambda value: self._employees.validate_inn(value, except_id=employee_id),
        )

    def _read_organization_inn(self) -> str:
        """Запрашивает ИНН предприятия допустимой длины."""

        def validate(value: str) -> None:
            """Проверяет цифровой формат ИНН предприятия."""

            if len(value) not in (10, 12) or not value.isascii() or not value.isdigit():
                raise ValueError("ИНН организации должен содержать 10 или 12 цифр")

        return self._reader.read_checked(
            lambda: self._reader.read_non_empty("ИНН организации: "),
            validate,
        )

    def _read_kpp(self, inn: str) -> str:
        """Запрашивает КПП с учётом введённого ИНН организации."""

        def validate(value: str) -> None:
            """Проверяет формат КПП и отсутствие КПП у ИП."""

            if len(inn) == 12 and value:
                raise ValueError("для ИП с 12-значным ИНН оставьте КПП пустым")
            if value and (
                len(value) != 9 or not value.isascii() or not value.isdigit()
            ):
                raise ValueError("КПП должен содержать 9 цифр или быть пустым")

        return self._reader.read_checked(
            lambda: self._reader.read_optional("КПП (для ИП оставьте пустым): "),
            validate,
        )

    def _read_position(self) -> str:
        """Запрашивает существующую должность предприятия."""

        return self._reader.read_checked(
            lambda: self._reader.read_non_empty("должность: "),
            self._organization.get_position,
        )

    def _read_employee_id(self, allowed_ids: tuple[int, ...] | None = None) -> int:
        """Запрашивает существующего сотрудника, при необходимости из табеля."""

        def validate(value: int) -> None:
            """Проверяет существование сотрудника и доступность в табеле."""

            self._employees.get_employee_by_id(value)
            if allowed_ids is not None and value not in allowed_ids:
                raise ValueError("сотрудника нет в табеле выбранного периода")

        return self._reader.read_checked(
            lambda: self._reader.read_int("ID сотрудника: ", 1),
            validate,
        )

    def _read_hire_date(self, dismissal_date: date | None = None) -> date:
        """Запрашивает дату приёма с учётом существующего увольнения."""

        def validate(value: date) -> None:
            """Не допускает приём позже записанного увольнения."""

            if dismissal_date is not None and value > dismissal_date:
                raise ValueError("дата приёма не может быть позже даты увольнения")

        return self._reader.read_checked(
            lambda: self._reader.read_date("дата приёма (ДД.ММ.ГГГГ): "),
            validate,
        )

    def _read_rate(self) -> Decimal:
        """Запрашивает допустимую положительную ставку за смену."""

        def validate(value: Decimal) -> None:
            """Проверяет предел ставки и точность до копеек."""

            if value > Decimal("1000000000"):
                raise ValueError("ставка за смену слишком велика")
            if value <= 0 or value != value.quantize(Decimal("0.01")):
                raise ValueError("ставка должна быть положительной, до копеек")

        return self._reader.read_checked(
            lambda: self._reader.read_decimal("базовая ставка за смену: "),
            validate,
        )

    def _read_seniority_percent(self) -> Decimal:
        """Запрашивает надбавку за год стажа в допустимом диапазоне."""

        def validate(value: Decimal) -> None:
            """Ограничивает надбавку диапазоном от нуля до ста процентов."""

            if value > 100:
                raise ValueError("надбавка должна быть от 0 до 100%")

        return self._reader.read_checked(
            lambda: self._reader.read_decimal("надбавка за год стажа (%): "),
            validate,
        )

    def _configure_organization(self) -> None:
        """Последовательно запрашивает и сохраняет реквизиты предприятия."""

        name = self._reader.read_non_empty("название организации: ")
        inn = self._read_organization_inn()
        kpp = self._read_kpp(inn)
        address = self._reader.read_non_empty("адрес: ")

        organization = self._organization.set_organization(
            name=name,
            inn=inn,
            kpp=kpp,
            address=address,
        )
        self._output(f"настройки организации «{organization.name}» сохранены")

    def _configure_position(self) -> None:
        """Запрашивает должность и проверяет каждый параметр тарифа."""

        self._organization.get_organization()
        name = self._reader.read_non_empty("должность: ")
        base_rate = self._read_rate()
        seniority_percent = self._read_seniority_percent()

        position = self._organization.set_position(
            name=name,
            base_rate=base_rate,
            seniority_percent=seniority_percent,
        )
        self._output(
            f"должность «{position.name}»: {position.base_rate:.2f} руб. за смену"
        )

    def _add_employee(self) -> None:
        """Запрашивает поля сотрудника с сохранением уже проверенных значений."""

        self._organization.get_organization()
        self._show_positions()

        full_name = self._reader.read_non_empty("ФИО: ")
        inn = self._read_inn()
        position = self._read_position()
        hire_date = self._read_hire_date()
        experience_years = self._reader.read_int("стаж в полных годах: ", 0, 80)

        employee = self._employees.add_employee(
            full_name=full_name,
            inn=inn,
            position=position,
            hire_date=hire_date,
            experience_years=experience_years,
        )
        self._output(
            f"сотрудник добавлен, ID: {employee.employee_id}; "
            f"ставка: {employee.rate_per_shift:.2f} руб."
        )

    def _show_positions(self) -> None:
        """Показывает доступные тарифы предприятия."""

        positions = self._organization.list_positions()
        if not positions:
            raise ValueError("сначала добавьте хотя бы одну должность")
        for position in positions:
            self._output(
                f"{position.name}: {position.base_rate:.2f} руб., "
                f"надбавка {position.seniority_percent}% за год стажа"
            )

    def _edit_employee(self) -> None:
        """Проверяет каждое новое значение перед обновлением карточки."""

        employee_id = self._read_employee_id()
        current = self._employees.get_employee_by_id(employee_id)
        self._output(format_employees([current]))
        self._show_positions()

        full_name = self._reader.read_non_empty("новое ФИО: ")
        inn = self._read_inn(employee_id)
        position = self._read_position()
        hire_date = self._read_hire_date(current.dismissal_date)
        experience_years = self._reader.read_int("стаж в полных годах: ", 0, 80)

        updated = self._employees.update_employee(
            employee_id,
            full_name,
            inn,
            position,
            hire_date,
            experience_years,
        )
        self._output(f"карточка ID {updated.employee_id} обновлена")

    def _dismiss_employee(self) -> None:
        """Запрашивает сотрудника и допустимую дату увольнения."""

        def validate_employee(value: int) -> None:
            """Не допускает повторное увольнение сотрудника."""

            employee = self._employees.get_employee_by_id(value)
            if employee.dismissal_date is not None:
                raise ValueError("сотрудник уже уволен; выберите другого")

        employee_id = self._reader.read_checked(
            self._read_employee_id,
            validate_employee,
        )
        current = self._employees.get_employee_by_id(employee_id)

        def validate_date(value: date) -> None:
            """Проверяет дату увольнения относительно даты приёма."""

            if value < current.hire_date:
                raise ValueError("увольнение не может быть раньше приёма на работу")

        dismissal_date = self._reader.read_checked(
            lambda: self._reader.read_date("дата увольнения (ДД.ММ.ГГГГ): "),
            validate_date,
        )
        employee = self._employees.dismiss_employee(employee_id, dismissal_date)
        self._output(f"сотрудник {employee.full_name} уволен")

    def _show_employees(self) -> None:
        """Выводит справочник сотрудников."""

        self._output(format_employees(self._employees.get_all_employees()))

    def _set_calendar_norm(self) -> None:
        """Сохраняет норму для нестандартного графика до создания табеля."""

        period = self._period()
        try:
            self._timesheets.get(period)
        except LookupError:
            pass
        else:
            raise ValueError("табель уже создан; норма периода зафиксирована")
        norm = self._reader.read_int("норма смен за месяц: ", 1, period.end.day)
        self._calendar.set_norm(period, norm)
        self._output(f"норма {norm} смен сохранена для {period}")

    def _open_timesheet(self) -> None:
        """Создаёт либо открывает табель и показывает его строки."""

        self._organization.get_organization()
        period = self._period()
        timesheet = self._timesheets.generate(period)
        self._output(format_timesheet(timesheet, self._employees.get_all_employees()))

    def _fill_timesheet(self) -> None:
        """Проверяет каждое поле строки с учётом оставшейся нормы."""

        period = self._existing_period(self._timesheets.get)
        timesheet = self._timesheets.get(period)
        if timesheet.closed:
            raise ValueError("расчётный период закрыт")

        self._output(format_timesheet(timesheet, self._employees.get_all_employees()))
        employee_id = self._read_employee_id(timesheet.employee_ids)

        shifts = self._reader.read_int("отработано смен: ", 0, timesheet.shift_norm)
        sick_days = self._reader.read_int(
            "больничный (дней): ", 0, timesheet.shift_norm - shifts
        )
        vacation_days = self._reader.read_int(
            "отпуск (дней): ", 0, timesheet.shift_norm - shifts - sick_days
        )

        entry = self._timesheets.fill(
            period, employee_id, shifts, sick_days, vacation_days
        )
        self._output(f"строка сохранена; всего учтено: {entry.total_days}")

    def _calculate_statement(self) -> None:
        """Запускает расчёт месяца с подтверждением повторного расчёта."""

        period = self._existing_period(self._timesheets.get)
        replace_existing = False
        try:
            self._payroll.get_statement(period)
        except LookupError:
            pass
        else:
            replace_existing = self._reader.confirm(
                "ведомость уже существует, пересчитать?"
            )
            if not replace_existing:
                self._output("расчёт отменён; старая ведомость сохранена")
                return
        statement = self._payroll.calculate_period(period, replace_existing)
        self._output(format_statement(statement, True))

    def _show_statement(self) -> None:
        """Показывает ведомость и её актуальность после изменения табеля."""

        period = self._existing_period(self._payroll.get_statement)
        statement = self._payroll.get_statement(period)
        self._output(format_statement(statement, self._payroll.is_current(period)))

    def _show_payslip(self) -> None:
        """Показывает текстовый расчётный листок выбранного работника."""

        period = self._existing_period(self._payroll.get_statement)
        employee_id = self._reader.read_checked(
            self._read_employee_id,
            lambda value: self._payroll.get_payslip(period, value),
        )
        result = self._payroll.get_payslip(period, employee_id)
        statement = self._payroll.get_statement(period)
        if not self._payroll.is_current(period):
            self._output("внимание: табель изменён, листок требует перерасчёта")
        self._output(format_payslip(result, statement))

    def _close_period(self) -> None:
        """Закрывает проверенный период после подтверждения бухгалтера."""

        period = self._existing_period(self._timesheets.get)
        if self._reader.confirm(f"закрыть расчётный период {period}?"):
            self._payroll.close_period(period)
            self._output(f"период {period} закрыт")

    def _stop(self) -> None:
        """Завершает сеанс и освобождает временные данные."""

        self._running = False
        self._output("работа программы завершена")
