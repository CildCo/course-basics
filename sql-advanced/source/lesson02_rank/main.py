import csv
import sqlite3
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


SCHEMA = """
CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region        TEXT NOT NULL,
    level         TEXT NOT NULL,
    joined_at     TEXT NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  TEXT NOT NULL,
    category    TEXT NOT NULL,
    product     TEXT NOT NULL,
    units       INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    status      TEXT NOT NULL
);
"""


def read_customers():
    with data_path("customers.csv").open(encoding="utf-8", newline="") as f:
        return [
            (int(row["customer_id"]), row["customer_name"], row["region"], row["level"], row["joined_at"])
            for row in csv.DictReader(f)
        ]


def read_orders():
    with data_path("orders.csv").open(encoding="utf-8", newline="") as f:
        return [
            (
                int(row["order_id"]),
                int(row["customer_id"]),
                row["order_date"],
                row["category"],
                row["product"],
                int(row["units"]),
                float(row["unit_price"]),
                row["status"],
            )
            for row in csv.DictReader(f)
        ]


def load_shop():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", read_customers())
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", read_orders())
    conn.commit()
    return conn


def show(conn, sql, limit=None):
    cursor = conn.execute(sql)
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    if limit is not None:
        rows = rows[:limit]
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join("" if value is None else str(value) for value in row))
    print(f"({len(rows)} 行)")


print("SQLite", sqlite3.sqlite_version)


conn = load_shop()

show(conn, """
WITH scores(name, score) AS (
    VALUES ('甲', 90), ('乙', 90), ('丙', 80), ('丁', 70)
)
SELECT name,
       score,
       ROW_NUMBER() OVER (ORDER BY score DESC) AS row_number,
       RANK()       OVER (ORDER BY score DESC) AS rank,
       DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rank
FROM scores
""")


show(conn, """
WITH customer_revenue AS (
    SELECT c.customer_id,
           c.customer_name,
           c.region,
           ROUND(SUM(o.units * o.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.customer_id
)
SELECT customer_name,
       region,
       revenue,
       ROW_NUMBER() OVER (ORDER BY revenue DESC) AS row_number,
       RANK()       OVER (ORDER BY revenue DESC) AS rank
FROM customer_revenue
ORDER BY revenue DESC
""")


show(conn, """
WITH category_revenue AS (
    SELECT c.customer_name,
           o.category,
           ROUND(SUM(o.units * o.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.customer_id, o.category
),
ranked AS (
    SELECT customer_name,
           category,
           revenue,
           ROW_NUMBER() OVER (
               PARTITION BY category
               ORDER BY revenue DESC, customer_name
           ) AS position
    FROM category_revenue
)
SELECT category, customer_name, revenue, position
FROM ranked
WHERE position <= 3
ORDER BY category, position
""")
