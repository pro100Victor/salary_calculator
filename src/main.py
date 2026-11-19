from collections.abc import Callable

from salary_calculator.cli.input_helpers import InputReader

from salary_calculator.application.factory import create_provider
from salary_calculator.application.provider import ServiceProvider
from salary_calculator.cli import SalaryCalculatorCLI
from salary_calculator.services.auth import AuthService


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
