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
SELECT month, customer_name, revenue, position
FROM (
    SELECT month,
           customer_name,
           revenue,
           ROW_NUMBER() OVER (
               PARTITION BY month ORDER BY revenue DESC, customer_name
           ) AS position
    FROM (
        SELECT substr(o.order_date, 1, 7) AS month,
               c.customer_name,
               ROUND(SUM(o.units * o.unit_price), 2) AS revenue
        FROM orders AS o
        JOIN customers AS c ON c.customer_id = o.customer_id
        WHERE o.status = 'completed'
        GROUP BY month, c.customer_id
    )
)
WHERE position <= 2
ORDER BY month, position
""")


show(conn, """
WITH monthly_customer AS (
    SELECT substr(o.order_date, 1, 7) AS month,
           c.customer_name,
           ROUND(SUM(o.units * o.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY month, c.customer_id
),
ranked AS (
    SELECT month,
           customer_name,
           revenue,
           ROW_NUMBER() OVER (
               PARTITION BY month ORDER BY revenue DESC, customer_name
           ) AS position
    FROM monthly_customer
)
SELECT month, customer_name, revenue, position
FROM ranked
WHERE position <= 2
ORDER BY month, position
""")


show(conn, """
WITH monthly_customer AS (
    SELECT substr(o.order_date, 1, 7) AS month,
           c.customer_name,
           ROUND(SUM(o.units * o.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY month, c.customer_id
),
monthly_total AS (
    SELECT month, ROUND(SUM(revenue), 2) AS total_revenue
    FROM monthly_customer
    GROUP BY month
),
ranked AS (
    SELECT month,
           customer_name,
           revenue,
           ROW_NUMBER() OVER (
               PARTITION BY month ORDER BY revenue DESC, customer_name
           ) AS position
    FROM monthly_customer
)
SELECT r.month,
       r.customer_name,
       r.revenue,
       t.total_revenue,
       ROUND(r.revenue * 100.0 / t.total_revenue, 2) AS share_percent
FROM ranked AS r
JOIN monthly_total AS t ON t.month = r.month
WHERE r.position = 1
ORDER BY r.month
""")
