# Семейный бюджет

Десктопное приложение (PyQt6 + PostgreSQL + matplotlib): статьи, операции, балансы, графики, экспорт отчётов в txt.

## Запуск

Нужен Python 3.10+ и PostgreSQL (проще всего через Docker).

```bash
# 1. зависимости
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. база (пароль суперпользователя postgres = admin)
docker compose up -d
python setup_db.py --seed          # создаст БД budget, таблицы, процедуры, роли; --seed = демо-данные

# 3. приложение
python course.py
```

Без Docker: поставь Postgres сам и запусти `setup_db.py` (спросит пароль суперпользователя
или возьмёт из `PGPASSWORD`). Хост/порт/имя БД лежат в `cfg.ini`.

## Логины

Вход в приложение = логин/пароль роли Postgres. В `cfg.ini` лежат sha256-хеши:

| роль | логин | пароль | права |
|------|-------|--------|-------|
| root | `postgres` | `admin` | всё |
| user | `user` | `password` | только чтение |

Свои логины: поменяй хеши в `cfg.ini` (`python -c "import hashlib;print(hashlib.sha256(b'логин').hexdigest())"`)
и создай соответствующие роли в Postgres.

## Файлы

- `course.py` - всё приложение
- `schema.sql` - таблицы, типы, процедуры (`insert_balance`, `print_amounts`, `print_debit_credit_on_period`, `calculate_percents_flow_p`)
- `seed.sql` - демо-данные
- `setup_db.py` - применяет схему и создаёт роли (можно запускать повторно)
