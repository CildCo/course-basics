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
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS month,
           ROUND(SUM(units * unit_price), 2) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY month
)
SELECT month, revenue
FROM monthly
ORDER BY month
""")


show(conn, """
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS month,
           ROUND(SUM(units * unit_price), 2) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY month
)
SELECT month,
       revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2) AS running_total,
       ROUND(AVG(revenue) OVER (
           ORDER BY month
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 2) AS moving_avg_3
FROM monthly
ORDER BY month
""")


show(conn, """
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS month,
           ROUND(SUM(units * unit_price), 2) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY month
)
SELECT month,
       revenue,
       LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
       ROUND(
           (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0
           / LAG(revenue) OVER (ORDER BY month),
           2
       ) AS mom_percent
FROM monthly
ORDER BY month
""")


show(conn, """
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS month,
           ROUND(SUM(units * unit_price), 2) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY month
)
SELECT month,
       revenue,
       ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2) AS share_percent
FROM monthly
ORDER BY month
""")
