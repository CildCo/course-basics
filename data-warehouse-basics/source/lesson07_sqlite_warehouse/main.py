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

db_path = out / "warehouse.db"
db_path.unlink(missing_ok=True)
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript("""
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    year_month TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    month INTEGER NOT NULL,
    weekday INTEGER NOT NULL
);
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    segment TEXT NOT NULL
);
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL UNIQUE,
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
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    gross_amount REAL NOT NULL CHECK (gross_amount >= 0),
    net_amount REAL NOT NULL CHECK (net_amount >= 0),
    status TEXT NOT NULL,
    channel TEXT NOT NULL
);
CREATE INDEX idx_fact_date ON fact_orders(date_key);
CREATE INDEX idx_fact_customer ON fact_orders(customer_key);
CREATE INDEX idx_fact_product ON fact_orders(product_key);
""")
conn.executemany(
    "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?)",
    [(int(r["date_id"]), r["date"], r["year_month"], int(r["year"]), r["quarter"], int(r["month"]), int(r["weekday"])) for r in calendar],
)
conn.executemany(
    "INSERT INTO dim_customer VALUES (?, ?, ?, ?, ?)",
    [(index, r["customer_id"], r["customer_name"], r["city"], r["segment"]) for index, r in enumerate(customers, 1)],
)
conn.executemany(
    "INSERT INTO dim_product VALUES (?, ?, ?, ?, ?, ?)",
    [(index, r["product_id"], r["product_name"], r["category"], float(r["list_price"]), float(r["cost"])) for index, r in enumerate(products, 1)],
)
customer_key = {r["customer_id"]: index for index, r in enumerate(customers, 1)}
product_key = {r["product_id"]: index for index, r in enumerate(products, 1)}
fact_rows = []
for order in orders:
    gross = round(int(order["quantity"]) * float(order["unit_price"]), 2)
    fact_rows.append(
        (
            order["order_id"],
            int(order["order_date"].replace("-", "")),
            customer_key[order["customer_id"]],
            product_key[order["product_id"]],
            int(order["quantity"]),
            gross,
            round(gross - float(order["discount_amount"]), 2),
            order["status"],
            order["channel"],
        )
    )
conn.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", fact_rows)
conn.commit()

print("表:", [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")])
print("事实表索引:", [r[1] for r in conn.execute("PRAGMA index_list(fact_orders)")])
print("事实行数:", conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0])


conn.executescript("""
CREATE VIEW v_monthly_sales AS
SELECT d.year_month,
       COUNT(*) AS orders,
       ROUND(SUM(f.net_amount), 2) AS net_amount
FROM fact_orders f
JOIN dim_date d ON d.date_key = f.date_key
WHERE f.status IN ('completed', 'paid')
GROUP BY d.year_month;

CREATE VIEW v_category_share AS
SELECT category,
       net_amount,
       ROUND(100.0 * net_amount / SUM(net_amount) OVER (), 2) AS share_pct
FROM (
    SELECT p.category AS category,
           ROUND(SUM(f.net_amount), 2) AS net_amount
    FROM fact_orders f
    JOIN dim_product p ON p.product_key = f.product_key
    WHERE f.status IN ('completed', 'paid')
    GROUP BY p.category
);
""")
print("最近 6 个月：")
show(conn.execute("SELECT * FROM v_monthly_sales ORDER BY year_month DESC LIMIT 6"))
print()
print("品类贡献：")
show(conn.execute("SELECT * FROM v_category_share ORDER BY net_amount DESC"))


plan = conn.execute(
    "EXPLAIN QUERY PLAN SELECT * FROM fact_orders INDEXED BY idx_fact_customer WHERE customer_key = ?",
    (7,),
).fetchall()
for row in plan:
    print("查询计划:", row[-1])

show(
    conn.execute(
        """
        SELECT c.customer_name, c.city, COUNT(*) AS orders, ROUND(SUM(f.net_amount), 2) AS net_amount
        FROM fact_orders f INDEXED BY idx_fact_customer
        JOIN dim_customer c ON c.customer_key = f.customer_key
        WHERE f.customer_key = 7 AND f.status IN ('completed', 'paid')
        GROUP BY c.customer_name, c.city
        """
    )
)
print()
print("外键检查:", conn.execute("PRAGMA foreign_key_check").fetchall())
print("重复订单:", conn.execute("SELECT COUNT(*) FROM (SELECT order_id FROM fact_orders GROUP BY order_id HAVING COUNT(*) > 1)").fetchone()[0])
