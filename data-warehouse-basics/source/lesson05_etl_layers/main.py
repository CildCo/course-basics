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


db_path = out / "warehouse.db"
db_path.unlink(missing_ok=True)
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
print("数据库文件:", db_path.name)


fig, ax = plt.subplots(figsize=(11, 3.8))
ax.set_xlim(0, 11)
ax.set_ylim(0, 4)
ax.axis("off")
layers = [
    ("ODS", "贴源层", "原样保存\nCSV / 业务库", "#fee2e2"),
    ("DWD", "明细层", "去重、清洗\n星型模型", "#dbeafe"),
    ("DWS", "汇总层", "按天 / 品类\n轻度聚合", "#dcfce7"),
    ("ADS", "应用层", "月报、排行\n接口指标", "#fef3c7"),
]
for index, (name, role, detail, color) in enumerate(layers):
    x = 0.3 + index * 2.7
    rect = plt.Rectangle((x, 1.1), 2.2, 2.0, facecolor=color, edgecolor="#334155", linewidth=1.4)
    ax.add_patch(rect)
    ax.text(x + 1.1, 2.72, name, ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(x + 1.1, 2.32, role, ha="center", va="center", fontsize=10, color="#475569")
    ax.text(x + 1.1, 1.75, detail, ha="center", va="center", fontsize=9, color="#334155")
    if index < len(layers) - 1:
        ax.annotate("", xy=(x + 2.55, 2.1), xytext=(x + 2.25, 2.1), arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.6))
ax.set_title("数仓分层：从贴源到应用", fontsize=14, pad=12)
fig.tight_layout()
fig.savefig(out / "warehouse-layers.png", dpi=130, bbox_inches="tight")
display(Image(filename=str(out / "warehouse-layers.png")))
plt.close(fig)


orders = read_csv("orders.csv")
customers = read_csv("customers.csv")
products = read_csv("products.csv")
calendar = read_csv("calendar.csv")

raw_rows = [dict(row) for row in orders]
raw_rows.extend(dict(row) for row in orders[:3])
invalid = dict(orders[0])
invalid["order_id"] = "ORD_BAD"
invalid["quantity"] = "0"
raw_rows.append(invalid)

conn.executescript("""
CREATE TABLE ods_orders (
    order_id TEXT,
    order_date TEXT,
    customer_id TEXT,
    product_id TEXT,
    quantity TEXT,
    unit_price TEXT,
    discount_amount TEXT,
    status TEXT,
    channel TEXT,
    load_batch TEXT
);
CREATE TABLE ods_customers (
    customer_id TEXT,
    customer_name TEXT,
    city TEXT,
    segment TEXT,
    signup_date TEXT,
    load_batch TEXT
);
CREATE TABLE ods_products (
    product_id TEXT,
    product_name TEXT,
    category TEXT,
    list_price TEXT,
    cost TEXT,
    load_batch TEXT
);
CREATE TABLE ods_calendar (
    date_id TEXT,
    date TEXT,
    year TEXT,
    quarter TEXT,
    month TEXT,
    year_month TEXT,
    weekday TEXT,
    is_weekend TEXT,
    load_batch TEXT
);
""")
batch = "2026-09-30"
conn.executemany(
    "INSERT INTO ods_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [
        (r["order_id"], r["order_date"], r["customer_id"], r["product_id"], r["quantity"], r["unit_price"], r["discount_amount"], r["status"], r["channel"], batch)
        for r in raw_rows
    ],
)
conn.executemany(
    "INSERT INTO ods_customers VALUES (?, ?, ?, ?, ?, ?)",
    [(r["customer_id"], r["customer_name"], r["city"], r["segment"], r["signup_date"], batch) for r in customers],
)
conn.executemany(
    "INSERT INTO ods_products VALUES (?, ?, ?, ?, ?, ?)",
    [(r["product_id"], r["product_name"], r["category"], r["list_price"], r["cost"], batch) for r in products],
)
conn.executemany(
    "INSERT INTO ods_calendar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [(r["date_id"], r["date"], r["year"], r["quarter"], r["month"], r["year_month"], r["weekday"], r["is_weekend"], batch) for r in calendar],
)
conn.commit()
print("ODS 订单行数:", conn.execute("SELECT COUNT(*) FROM ods_orders").fetchone()[0])
print("ODS 客户行数:", conn.execute("SELECT COUNT(*) FROM ods_customers").fetchone()[0])
print("ODS 商品行数:", conn.execute("SELECT COUNT(*) FROM ods_products").fetchone()[0])
print("ODS 日期行数:", conn.execute("SELECT COUNT(*) FROM ods_calendar").fetchone()[0])


valid_status = {"completed", "paid", "refunded", "cancelled"}
seen = set()
clean_orders = []
for row in raw_rows:
    order_id = row["order_id"]
    if order_id in seen:
        continue
    if int(float(row["quantity"])) <= 0:
        continue
    if row["status"] not in valid_status:
        continue
    seen.add(order_id)
    clean_orders.append(row)

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
CREATE TABLE dwd_fact_orders (
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
for order in clean_orders:
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
conn.executemany("INSERT INTO dwd_fact_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fact_rows)
conn.commit()
print("清洗后订单数:", len(clean_orders))
print("DWD 事实行数:", conn.execute("SELECT COUNT(*) FROM dwd_fact_orders").fetchone()[0])
print("维表行数:", conn.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0], conn.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0], conn.execute("SELECT COUNT(*) FROM dim_product").fetchone()[0])


conn.executescript("""
CREATE TABLE dws_daily_category (
    date_key INTEGER NOT NULL,
    category TEXT NOT NULL,
    orders INTEGER NOT NULL,
    units INTEGER NOT NULL,
    net_amount REAL NOT NULL,
    PRIMARY KEY (date_key, category)
);
CREATE TABLE ads_monthly_metrics (
    year_month TEXT PRIMARY KEY,
    gmv REAL NOT NULL,
    paid_amount REAL NOT NULL,
    net_revenue REAL NOT NULL,
    valid_orders INTEGER NOT NULL,
    completed_orders INTEGER NOT NULL
);
""")
conn.execute(
    """
    INSERT INTO dws_daily_category
    SELECT f.date_key,
           p.category,
           COUNT(*) AS orders,
           SUM(f.quantity) AS units,
           ROUND(SUM(f.net_amount), 2) AS net_amount
    FROM dwd_fact_orders f
    JOIN dim_product p ON p.product_key = f.product_key
    WHERE f.status IN ('completed', 'paid')
    GROUP BY f.date_key, p.category
    """
)
conn.execute(
    """
    INSERT INTO ads_monthly_metrics
    SELECT d.year_month,
           ROUND(SUM(CASE WHEN f.status <> 'cancelled' THEN f.gross_amount ELSE 0 END), 2) AS gmv,
           ROUND(SUM(CASE WHEN f.status IN ('completed', 'paid') THEN f.net_amount ELSE 0 END), 2) AS paid_amount,
           ROUND(SUM(CASE WHEN f.status = 'completed' THEN f.net_amount ELSE 0 END), 2) AS net_revenue,
           SUM(CASE WHEN f.status IN ('completed', 'paid') THEN 1 ELSE 0 END) AS valid_orders,
           SUM(CASE WHEN f.status = 'completed' THEN 1 ELSE 0 END) AS completed_orders
    FROM dwd_fact_orders f
    JOIN dim_date d ON d.date_key = f.date_key
    GROUP BY d.year_month
    """
)
conn.commit()
print("DWS 日品类行数:", conn.execute("SELECT COUNT(*) FROM dws_daily_category").fetchone()[0])
print("ADS 月份数:", conn.execute("SELECT COUNT(*) FROM ads_monthly_metrics").fetchone()[0])
show(conn.execute("SELECT * FROM ads_monthly_metrics ORDER BY year_month DESC LIMIT 6"))
