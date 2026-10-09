"""Создаёт БД, таблицы, процедуры и роли для приложения.

Использование:
    python setup_db.py [--seed]

Параметры подключения (host/port/dbname) берутся из cfg.ini.
Суперпользователь Postgres: переменные PGUSER (по умолчанию postgres) и PGPASSWORD;
если PGPASSWORD не задан - спросит пароль.
Роли приложения: root-вход = postgres/admin, обычный = user/password (под хеши из cfg.ini).
Скрипт можно запускать повторно.
"""
import argparse
import configparser
import getpass
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="залить демо-данные")
    ap.add_argument("--app-user", default="user", help="имя обычной роли (по умолчанию user)")
    ap.add_argument("--app-password", default="password", help="пароль обычной роли")
    args = ap.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(os.environ.get("BUDGET_CFG", HERE / "cfg.ini"))
    host, port, dbname = cfg["db"]["host"], cfg["db"]["port"], cfg["db"]["dbname"]

    admin = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD") or getpass.getpass(f"Пароль Postgres для {admin}: ")

    def conninfo(db):
        return make_conninfo(host=host, port=port, dbname=db, user=admin, password=password)

    # 1. база
    with psycopg.connect(conninfo("postgres"), autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            print(f"База {dbname} создана")

    # 2. схема, роль, права
    with psycopg.connect(conninfo(dbname), autocommit=True) as conn:
        conn.execute((HERE / "schema.sql").read_text(encoding="utf-8"))
        print("Схема применена")

        role = sql.Identifier(args.app_user)
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (args.app_user,)).fetchone():
            conn.execute(sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(role, sql.Literal(args.app_password)))
        else:
            conn.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(role, sql.Literal(args.app_password)))
        conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(dbname), role))
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
        # обычный пользователь - только чтение
        conn.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(role))
        print(f"Роль {args.app_user} готова (только чтение)")

        if args.seed:
            conn.execute((HERE / "seed.sql").read_text(encoding="utf-8"))
            print("Демо-данные загружены")


if __name__ == "__main__":
    main()
