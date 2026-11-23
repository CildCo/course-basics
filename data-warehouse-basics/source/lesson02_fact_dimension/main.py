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


calendar = read_csv("calendar.csv")
customers = read_csv("customers.csv")
products = read_csv("products.csv")
orders = read_csv("orders.csv")

conn = sqlite3.connect(":memory:")
conn.executescript("""
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    month INTEGER NOT NULL,
    year_month TEXT NOT NULL,
    weekday INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL
);
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    segment TEXT NOT NULL,
    signup_date TEXT NOT NULL
);
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_price REAL NOT NULL,
    cost REAL NOT NULL
);
CREATE TABLE fact_orders (
    order_id TEXT PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key INTEGER NOT NULL REFERENCES dim_product(product_key),
    quantity INTEGER NOT NULL,
    gross_amount REAL NOT NULL,
    discount_amount REAL NOT NULL,
    net_amount REAL NOT NULL,
    status TEXT NOT NULL,
    channel TEXT NOT NULL
);
""")

conn.executemany(
    "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    [
        (int(r["date_id"]), r["date"], int(r["year"]), r["quarter"], int(r["month"]), r["year_month"], int(r["weekday"]), int(r["is_weekend"]))
        for r in calendar
    ],
)
conn.executemany(
    "INSERT INTO dim_customer VALUES (?, ?, ?, ?, ?, ?)",
    [
        (index, r["customer_id"], r["customer_name"], r["city"], r["segment"], r["signup_date"])
        for index, r in enumerate(customers, 1)
    ],
)
conn.executemany(
    "INSERT INTO dim_product VALUES (?, ?, ?, ?, ?, ?)",
    [
        (index, r["product_id"], r["product_name"], r["category"], float(r["list_price"]), float(r["cost"]))
        for index, r in enumerate(products, 1)
    ],
)

customer_key = {r["customer_id"]: index for index, r in enumerate(customers, 1)}
product_key = {r["product_id"]: index for index, r in enumerate(products, 1)}
fact_rows = []
for order in orders:
    gross = round(int(order["quantity"]) * float(order["unit_price"]), 2)
    discount = float(order["discount_amount"])
    fact_rows.append(
        (
            order["order_id"],
            int(order["order_date"].replace("-", "")),
            customer_key[order["customer_id"]],
            product_key[order["product_id"]],
            int(order["quantity"]),
            gross,
            discount,
            round(gross - discount, 2),
            order["status"],
            order["channel"],
        )
    )
conn.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fact_rows)
conn.commit()

print("日期维表:", conn.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0])
print("客户维表:", conn.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0])
print("商品维表:", conn.execute("SELECT COUNT(*) FROM dim_product").fetchone()[0])
rows = conn.execute("SELECT COUNT(*), COUNT(DISTINCT order_id) FROM fact_orders").fetchone()
print("事实行数:", rows[0], "去重订单数:", rows[1])
show(conn.execute("SELECT * FROM fact_orders ORDER BY order_id LIMIT 3"))


sql = """
SELECT d.year_month,
       p.category,
       COUNT(*) AS orders,
       ROUND(SUM(f.net_amount), 2) AS net_amount
FROM fact_orders f
JOIN dim_date d ON d.date_key = f.date_key
JOIN dim_product p ON p.product_key = f.product_key
WHERE f.status IN ('completed', 'paid')
GROUP BY d.year_month, p.category
ORDER BY d.year_month, net_amount DESC
LIMIT 12
"""
show(conn.execute(sql))


checks = [
    ("日期维表未匹配", "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_date d ON d.date_key = f.date_key WHERE d.date_key IS NULL"),
    ("客户维表未匹配", "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_customer c ON c.customer_key = f.customer_key WHERE c.customer_key IS NULL"),
    ("商品维表未匹配", "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_product p ON p.product_key = f.product_key WHERE p.product_key IS NULL"),
    ("金额为负", "SELECT COUNT(*) FROM fact_orders WHERE net_amount < 0"),
    ("重复订单", "SELECT COUNT(*) FROM (SELECT order_id FROM fact_orders GROUP BY order_id HAVING COUNT(*) > 1)"),
]
for label, sql in checks:
    print(f"{label}: {conn.execute(sql).fetchone()[0]}")
