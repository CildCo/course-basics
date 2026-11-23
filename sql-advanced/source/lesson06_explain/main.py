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

slow_sql = """
SELECT COUNT(*) AS orders
FROM orders
WHERE status = 'completed'
   AND order_date >= '2026-08-01'
"""


def show_plan(conn, sql):
    print("SQL:", " ".join(sql.split()))
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print("计划:", row[3])
    print()


show_plan(conn, slow_sql)
show(conn, slow_sql)


import time


def average_ms(conn, sql, repeat=800):
    start = time.perf_counter()
    for _ in range(repeat):
        conn.execute(sql).fetchone()
    return (time.perf_counter() - start) * 1000 / repeat


before_ms = average_ms(conn, slow_sql)
print(f"加索引前平均耗时: {before_ms:.3f} ms")


conn.execute("CREATE INDEX idx_orders_status_date ON orders(status, order_date)")
conn.commit()

show_plan(conn, slow_sql)
show(conn, "PRAGMA index_info('idx_orders_status_date')")


after_ms = average_ms(conn, slow_sql)
print(f"加索引后平均耗时: {after_ms:.3f} ms")
print(f"前后耗时比: {before_ms / after_ms:.2f}（大于 1 表示索引后更快）")
show(conn, slow_sql)
