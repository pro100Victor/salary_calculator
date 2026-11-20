from collections.abc import Callable

from payroll.application.factory import create_provider
from payroll.application.provider import ServiceProvider
from payroll.cli import SalaryCalculatorCLI
from payroll.cli.input_helpers import InputReader
from payroll.services.auth import AuthService


def create_application(
    reader: InputReader | None = None,
    output: Callable[[str], None] | None = None,
    provider: ServiceProvider | None = None,
) -> SalaryCalculatorCLI:
    """Передаёт интерфейсу провайдер; сервисы открываются на каждую команду."""

    return SalaryCalculatorCLI(
        AuthService(),
        reader=reader,
        output=output,
        provider=provider or create_provider(),
    )


def main() -> None:
    """Запускает приложение."""

    create_application().run()


if __name__ == "__main__":
    main()
