"""Точка запуска веб-интерфейса из корня проекта."""

import uvicorn

from salary_calculator.web.app import create_web_application


def main() -> None:
    """Запускает локальный учебный сервер в одном процессе."""

    uvicorn.run(create_web_application(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
