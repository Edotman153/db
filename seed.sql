-- Демо-данные (необязательно): python setup_db.py --seed
INSERT INTO articles (name) VALUES ('salary'), ('buy bread'), ('buy potato'), ('transport')
ON CONFLICT (name) DO NOTHING;

INSERT INTO operations (article_id, debit, credit, create_date)
SELECT a.id, v.debit, v.credit, v.d::timestamp
FROM (VALUES
    ('salary',     10000,    0, '2024-09-01'),
    ('buy bread',      0,  180, '2024-09-05'),
    ('buy potato',     0,   50, '2024-09-05'),
    ('transport',      0,  300, '2024-09-10'),
    ('salary',     10000,    0, '2024-10-01'),
    ('buy bread',      0,  180, '2024-10-11'),
    ('buy potato',     0,   50, '2024-10-11'),
    ('transport',      0,  400, '2024-10-12')
) AS v(name, debit, credit, d)
JOIN articles a ON a.name = v.name;
