-- Схема БД для приложения "Семейный бюджет" (course.py).
-- Восстановлена по тому, как её использует код: таблицы, типы и 4 хранимые процедуры.
-- Запускается через setup_db.py (можно и руками: psql -d budget -f schema.sql).

-- Даты в приложении вводятся как дд-мм-гггг
DO $$ BEGIN
    EXECUTE format('ALTER DATABASE %I SET datestyle = ''ISO, DMY''', current_database());
END $$;

CREATE TABLE IF NOT EXISTS articles (
    id   serial PRIMARY KEY,
    name text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS balance (
    id          serial PRIMARY KEY,
    create_date timestamp NOT NULL,
    debit       bigint NOT NULL DEFAULT 0,
    credit      bigint NOT NULL DEFAULT 0,
    amount      bigint NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS operations (
    id          serial PRIMARY KEY,
    article_id  integer REFERENCES articles(id) ON DELETE SET NULL,
    debit       bigint NOT NULL DEFAULT 0,
    credit      bigint NOT NULL DEFAULT 0,
    create_date timestamp NOT NULL,
    balance_id  integer REFERENCES balance(id) ON DELETE SET NULL
);

-- Составные типы: приложение разбирает их текстовое представление (см. pyplotShow в course.py),
-- поэтому порядок и типы полей менять нельзя.
DO $$ BEGIN CREATE TYPE amt_row AS (d timestamp, amount bigint);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE dc_row  AS (article_id integer, d timestamp, s bigint);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE pf_row  AS (article_id integer, pct numeric);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Закрыть баланс на дату: суммирует все ещё не закрытые операции до этой даты
CREATE OR REPLACE PROCEDURE insert_balance(close_date date)
LANGUAGE plpgsql AS $$
DECLARE
    new_id integer;
    d bigint;
    c bigint;
BEGIN
    SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0) INTO d, c
    FROM operations WHERE balance_id IS NULL AND create_date::date <= close_date;

    INSERT INTO balance (create_date, debit, credit, amount)
    VALUES (close_date, d, c, d - c) RETURNING id INTO new_id;

    UPDATE operations SET balance_id = new_id
    WHERE balance_id IS NULL AND create_date::date <= close_date;
END $$;

-- Динамика баланса: массив (дата, чистая прибыль)
CREATE OR REPLACE PROCEDURE print_amounts(INOUT result amt_row[] DEFAULT NULL)
LANGUAGE plpgsql AS $$
BEGIN
    SELECT COALESCE(array_agg(ROW(b.create_date, b.amount)::amt_row ORDER BY b.create_date), '{}')
    INTO result FROM balance b;
END $$;

-- Доходы/расходы по выбранным статьям за период.
-- flag: 2 - доходы, 3 - расходы, 6 - оба (считаем всё всегда, приложение берёт нужное).
-- Возвращает: доходы, расходы (по статье и дню) и список дней, в которые были операции.
CREATE OR REPLACE PROCEDURE print_debit_credit_on_period(
    flag integer, beg date, fin date, ids integer[],
    INOUT p_debit dc_row[] DEFAULT NULL,
    INOUT p_credit dc_row[] DEFAULT NULL,
    INOUT p_dates timestamp[] DEFAULT NULL)
LANGUAGE plpgsql AS $$
BEGIN
    SELECT COALESCE(array_agg(ROW(q.article_id, q.d, q.s)::dc_row ORDER BY q.article_id, q.d), '{}')
    INTO p_debit FROM (
        SELECT article_id, date_trunc('day', create_date) AS d, SUM(debit)::bigint AS s
        FROM operations
        WHERE create_date::date BETWEEN beg AND fin AND article_id = ANY(ids)
        GROUP BY 1, 2) q;

    SELECT COALESCE(array_agg(ROW(q.article_id, q.d, q.s)::dc_row ORDER BY q.article_id, q.d), '{}')
    INTO p_credit FROM (
        SELECT article_id, date_trunc('day', create_date) AS d, SUM(credit)::bigint AS s
        FROM operations
        WHERE create_date::date BETWEEN beg AND fin AND article_id = ANY(ids)
        GROUP BY 1, 2) q;

    SELECT COALESCE(array_agg(q.d ORDER BY q.d), '{}')
    INTO p_dates FROM (
        SELECT DISTINCT date_trunc('day', create_date) AS d
        FROM operations
        WHERE create_date::date BETWEEN beg AND fin AND article_id = ANY(ids)) q;
END $$;

-- Доли статей в потоке за период. flow: 'debit' | 'credit' | 'amount'.
-- Возвращает массив (id статьи, процент).
CREATE OR REPLACE PROCEDURE calculate_percents_flow_p(
    beg date, fin date, names text[], flow text,
    INOUT result pf_row[] DEFAULT NULL)
LANGUAGE plpgsql AS $$
DECLARE
    total numeric;
BEGIN
    IF flow NOT IN ('debit', 'credit', 'amount') THEN
        RAISE EXCEPTION 'unknown flow type: %', flow;
    END IF;

    CREATE TEMP TABLE _flow ON COMMIT DROP AS
    SELECT a.id AS article_id,
           COALESCE(SUM(CASE flow WHEN 'debit'  THEN o.debit
                                  WHEN 'credit' THEN o.credit
                                  ELSE o.debit - o.credit END), 0)::numeric AS v
    FROM articles a
    LEFT JOIN operations o ON o.article_id = a.id AND o.create_date::date BETWEEN beg AND fin
    WHERE a.name = ANY(names)
    GROUP BY a.id;

    SELECT COALESCE(SUM(v) FILTER (WHERE v > 0), 0) INTO total FROM _flow;

    SELECT COALESCE(array_agg(ROW(f.article_id, CASE WHEN total = 0 THEN 0
                                                    ELSE round(100 * f.v / total, 2) END)::pf_row
                              ORDER BY f.article_id), '{}')
    INTO result FROM _flow f;

    DROP TABLE _flow;
END $$;
