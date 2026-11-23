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
print("星型模型建立完成，事实行数:", conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0])


fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")

def box(x, y, w, h, title, lines, color):
    rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#334155", linewidth=1.4)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="center", fontsize=12, fontweight="bold")
    for index, line in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.62 - index * 0.26, line, ha="center", va="center", fontsize=9, color="#334155")

box(0.2, 3.7, 2.8, 1.5, "dim_customer 客户维", ["customer_key", "城市 / 会员等级"], "#dbeafe")
box(7.0, 3.7, 2.8, 1.5, "dim_product 商品维", ["product_key", "品类 / 名称 / 成本"], "#dcfce7")
box(3.6, 0.3, 2.8, 1.3, "dim_date 日期维", ["date_key", "年 / 季 / 月 / 星期"], "#fef3c7")
box(3.3, 2.4, 3.4, 1.7, "fact_orders 订单事实", ["order_id", "date_key / customer_key", "product_key", "数量 / 金额 / 状态"], "#e2e8f0")

ax.annotate("", xy=(3.25, 3.0), xytext=(3.0, 3.9), arrowprops=dict(arrowstyle="-|>", color="#1d4ed8", lw=1.4))
ax.annotate("", xy=(6.75, 3.0), xytext=(7.0, 3.9), arrowprops=dict(arrowstyle="-|>", color="#15803d", lw=1.4))
ax.annotate("", xy=(4.3, 2.4), xytext=(4.3, 1.6), arrowprops=dict(arrowstyle="-|>", color="#b45309", lw=1.4))
ax.annotate("", xy=(5.7, 2.4), xytext=(5.7, 1.6), arrowprops=dict(arrowstyle="-|>", color="#b45309", lw=1.4))
ax.text(3.0, 3.5, "customer_key", fontsize=8, color="#1d4ed8", rotation=55)
ax.text(6.85, 3.5, "product_key", fontsize=8, color="#15803d", rotation=-55)
ax.text(2.75, 1.95, "date_key", fontsize=8, color="#b45309")
ax.set_title("星型模型：一张事实表 + 多张维度表", fontsize=14, pad=12)
fig.tight_layout()
fig.savefig(out / "star-schema.png", dpi=130, bbox_inches="tight")
display(Image(filename=str(out / "star-schema.png")))
plt.close(fig)


sql = """
SELECT c.city,
       p.category,
       COUNT(*) AS orders,
       ROUND(SUM(f.net_amount), 2) AS net_amount
FROM fact_orders f
JOIN dim_customer c ON c.customer_key = f.customer_key
JOIN dim_product p ON p.product_key = f.product_key
WHERE f.status IN ('completed', 'paid')
GROUP BY c.city, p.category
ORDER BY net_amount DESC
LIMIT 12
"""
show(conn.execute(sql))


sql = """
SELECT c.city,
       ROUND(SUM(CASE WHEN p.category = '办公用品' THEN f.net_amount ELSE 0 END), 2) AS office,
       ROUND(SUM(CASE WHEN p.category = '数码配件' THEN f.net_amount ELSE 0 END), 2) AS digital,
       ROUND(SUM(CASE WHEN p.category = '家居生活' THEN f.net_amount ELSE 0 END), 2) AS home,
       ROUND(SUM(CASE WHEN p.category = '食品饮料' THEN f.net_amount ELSE 0 END), 2) AS food,
       ROUND(SUM(f.net_amount), 2) AS total
FROM fact_orders f
JOIN dim_customer c ON c.customer_key = f.customer_key
JOIN dim_product p ON p.product_key = f.product_key
WHERE f.status IN ('completed', 'paid')
GROUP BY c.city
ORDER BY total DESC
"""
show(conn.execute(sql))
