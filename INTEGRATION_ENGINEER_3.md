# Финальная сборка лабораторной работы №3

## Порядок объединения

1. Взять папку общего Git-репозитория проекта.
2. Поместить в корень `pyproject.toml`, `uv.lock` и `.gitignore` из части инженера 3.
3. Поместить `src/main.py` из части инженера 3 в общую папку `src`.
4. Объединить папку `src/salary_calculator` инженера 1 с папкой `src/salary_calculator` инженера 2.
5. Поместить все тесты трёх инженеров в общую папку `tests`.
6. Поместить документы инженера 3 в общую папку `docs`.
7. Объединить подготовленные разделы трёх инженеров с существующим `README.md`.

Папки с одинаковыми названиями необходимо объединять, а не заменять целиком.

## Итоговая структура проекта

```text
project/
├── src/
│   ├── main.py
│   └── salary_calculator/
│       ├── __init__.py
│       ├── models.py
│       ├── employee_service.py
│       ├── calculators.py
│       ├── payroll_service.py
│       └── cli/
│           ├── __init__.py
│           ├── app.py
│           ├── contracts.py
│           ├── input_helpers.py
│           └── presenters.py
├── tests/
│   ├── test_employee_service.py
│   ├── test_payroll_service.py
│   ├── test_cli.py
│   └── test_integration.py
├── docs/
│   ├── ARCHITECTURE_LAB3.md
│   └── TEST_PLAN_LAB3.md
├── README.md
├── pyproject.toml
├── uv.lock
└── .gitignore
```

## Установка и запуск

Из корня проекта выполнить:

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest
uv run python src/main.py
```

## Что не нужно подключать на этом этапе

В исходном коде нельзя импортировать FastAPI, SQLAlchemy, Alembic и Pydantic. Они зафиксированы в зависимостях только по формальному критерию лабораторной работы. База данных, Docker и веб-интерфейс для минимального CLI-прототипа не требуются.

Если после объединения возникает ошибка `ModuleNotFoundError`, необходимо проверить, что папка `salary_calculator` находится непосредственно внутри `src`, а запуск выполняется из корня проекта командой `uv run python src/main.py`.
