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


def show_plan(conn, sql):
    print("SQL:", " ".join(sql.split()))
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print("计划:", row[3])
    print()


query = "SELECT * FROM orders WHERE customer_id = 3"
show_plan(conn, query)
show(conn, query, limit=3)


conn.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
conn.commit()

show_plan(conn, query)
show(conn, "PRAGMA index_list('orders')")


conn.execute("CREATE INDEX idx_orders_date ON orders(order_date)")
conn.commit()

show_plan(conn, "SELECT * FROM orders WHERE order_date >= '2026-09-01'")
show_plan(conn, "SELECT * FROM orders ORDER BY order_date DESC LIMIT 5")


conn.execute("CREATE INDEX idx_orders_product ON orders(product)")
conn.execute("PRAGMA case_sensitive_like = ON")
conn.commit()

show_plan(conn, "SELECT * FROM orders WHERE substr(order_date, 1, 7) = '2026-09'")
show_plan(conn, "SELECT * FROM orders WHERE product LIKE '%耳机%'")
show_plan(conn, "SELECT * FROM orders WHERE product LIKE '耳机%'")
