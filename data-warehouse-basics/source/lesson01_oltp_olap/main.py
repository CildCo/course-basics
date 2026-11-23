import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import csv
import json
import sqlite3
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


def read_csv(name):
    with data_path(name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)


def show(cursor, limit=None):
    print(" | ".join(item[0] for item in cursor.description))
    rows = cursor.fetchall()
    for row in rows[:limit] if limit is not None else rows:
        print(" | ".join(str(value) for value in row))


customers = read_csv("customers.csv")
products = read_csv("products.csv")
orders = read_csv("orders.csv")

conn = sqlite3.connect(":memory:")
conn.executescript("""
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    segment TEXT NOT NULL,
    signup_date TEXT NOT NULL
);
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_price REAL NOT NULL,
    cost REAL NOT NULL
);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount_amount REAL NOT NULL,
    status TEXT NOT NULL,
    channel TEXT NOT NULL
);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
""")
conn.executemany(
    "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
    [(r["customer_id"], r["customer_name"], r["city"], r["segment"], r["signup_date"]) for r in customers],
)
conn.executemany(
    "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
    [(r["product_id"], r["product_name"], r["category"], float(r["list_price"]), float(r["cost"])) for r in products],
)
conn.executemany(
    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [
        (
            r["order_id"], r["order_date"], r["customer_id"], r["product_id"],
            int(r["quantity"]), float(r["unit_price"]), float(r["discount_amount"]),
            r["status"], r["channel"],
        )
        for r in orders
    ],
)
conn.commit()

print("客户数:", conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0])
print("商品数:", conn.execute("SELECT COUNT(*) FROM products").fetchone()[0])
print("订单数:", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
show(conn.execute("SELECT order_id, order_date, customer_id, product_id, quantity, status FROM orders ORDER BY order_date LIMIT 5"))


target = conn.execute("SELECT order_id FROM orders ORDER BY order_id LIMIT 1").fetchone()[0]
rounds = 3000
start = time.perf_counter()
for _ in range(rounds):
    conn.execute("SELECT * FROM orders WHERE order_id = ?", (target,)).fetchone()
point_ms = (time.perf_counter() - start) * 1000 / rounds
print(f"按主键读取一单：{point_ms:.3f} ms/次，共 {rounds} 次")
for row in conn.execute("EXPLAIN QUERY PLAN SELECT * FROM orders WHERE order_id = ?", (target,)):
    print("查询计划:", row[-1])


sql = """
SELECT p.category,
       COUNT(*) AS orders,
       SUM(o.quantity) AS units,
       ROUND(SUM(o.quantity * o.unit_price), 2) AS gross_amount
FROM orders o
JOIN products p ON p.product_id = o.product_id
WHERE o.status <> 'cancelled'
GROUP BY p.category
ORDER BY gross_amount DESC
"""
rounds = 30
start = time.perf_counter()
for _ in range(rounds):
    conn.execute(sql).fetchall()
scan_ms = (time.perf_counter() - start) * 1000 / rounds
print(f"按品类汇总一次：{scan_ms:.2f} ms，共 {rounds} 次")
show(conn.execute(sql))
