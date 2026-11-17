# HTTP-интерфейс для команды

Автоматическая схема после запуска: http://127.0.0.1:8000/docs . Её генерирует FastAPI из фактических обработчиков и входных схем.

Формат даты в запросе: `YYYY-MM-DD`. На экране: ДД.ММ.ГГГГ. ИНН/КПП — строки; ведущие нули сохраняются. Деньги и проценты тарифа отправляются строками. Денежные результаты также возвращаются строками, без float-расчётов в браузере.

| Метод и путь | Действие / тело |
| --- | --- |
| POST `/api/login` | username, password; устанавливает HttpOnly cookie. |
| POST `/api/logout` | Завершает текущий сеанс. |
| GET `/api/state` | organization или null, positions, employees со status, storage_mode. |
| PUT `/api/organization` | name, inn, kpp, address. |
| PUT `/api/positions` | name, base_rate, seniority_percent; существующее имя обновляет тариф. |
| GET `/api/rate?position=...&experience_years=...` | Серверная rate_per_shift для карточки. |
| POST `/api/employees` | full_name, inn, position, hire_date, experience_years. Код 201. |
| PUT `/api/employees/{id}` | Те же редактируемые поля. employee_id, rate_per_shift и status клиент не назначает. |
| POST `/api/employees/{id}/dismiss` | dismissal_date. Не удаляет карточку. |
| GET `/api/periods/{year}/{month}` | period, norm, timesheet или null, statement или null. |
| PUT `/api/periods/{year}/{month}/norm` | shifts — норма до создания табеля. |
| POST `/api/periods/{year}/{month}/timesheet` | Формирование/открытие табеля. |
| PUT `/api/periods/{year}/{month}/entries/{id}` | worked_shifts, sick_days, vacation_days — строгие целые. |
| POST `/api/periods/{year}/{month}/statement` | replace_existing: bool, по умолчанию false. |
| POST `/api/periods/{year}/{month}/close` | Закрытие после актуального расчёта. |

Листок строится из результата сотрудника в серверной ведомости, не пересчитывается отдельно в JS. В statement находятся results, source_revision, total_accrued, total_tax, total_to_pay, is_current. Каждый PayrollResult содержит снимок Employee и суммы существующего расчётного ядра. Просмотр листка использует уже загруженную ведомость; отдельный PDF endpoint не добавлен.

Ошибки:

```json
{"message": "сотрудник с таким ИНН уже существует", "fields": {"inn": "сотрудник с таким ИНН уже существует"}}
```

400 — тип/значение/бизнес-правило; 401 — вход; 404 — отсутствующая запись; 503 — StorageError. На границе Pydantic ошибки ввода приводятся к 400 по требованиям проекта. При ошибке поля форма не очищается. Для ошибок неизвестного поля/общей операции показывается общее сообщение.

Ни один маршрут напрямую не работает с PostgreSQL. Все бизнес-операции выполняются через ApplicationServices. Новые HTTP-схемы описывают транспортные типы, а не заменяют domain dataclass и их валидаторы.
