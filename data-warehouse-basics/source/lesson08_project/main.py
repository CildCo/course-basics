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

db_path = out / "sales_warehouse.db"
db_path.unlink(missing_ok=True)
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")

# ODS：原样装载，并故意放入 3 条重复订单和 1 条数量为 0 的异常订单
raw_rows = [dict(row) for row in orders]
raw_rows.extend(dict(row) for row in orders[:3])
invalid = dict(orders[0])
invalid["order_id"] = "ORD_BAD"
invalid["quantity"] = "0"
raw_rows.append(invalid)

conn.executescript("""
CREATE TABLE ods_orders (
    order_id TEXT, order_date TEXT, customer_id TEXT, product_id TEXT,
    quantity TEXT, unit_price TEXT, discount_amount TEXT, status TEXT,
    channel TEXT, load_batch TEXT
);
CREATE TABLE ods_customers (
    customer_id TEXT, customer_name TEXT, city TEXT, segment TEXT,
    signup_date TEXT, load_batch TEXT
);
CREATE TABLE ods_products (
    product_id TEXT, product_name TEXT, category TEXT,
    list_price TEXT, cost TEXT, load_batch TEXT
);
CREATE TABLE ods_calendar (
    date_id TEXT, date TEXT, year TEXT, quarter TEXT, month TEXT,
    year_month TEXT, weekday TEXT, is_weekend TEXT, load_batch TEXT
);
""")
batch = "2026-09-30"
conn.executemany(
    "INSERT INTO ods_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [(r["order_id"], r["order_date"], r["customer_id"], r["product_id"], r["quantity"], r["unit_price"], r["discount_amount"], r["status"], r["channel"], batch) for r in raw_rows],
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

# DWD：去重、过滤异常、建立星型模型
valid_status = {"completed", "paid", "refunded", "cancelled"}
seen = set()
clean_orders = []
for row in raw_rows:
    if row["order_id"] in seen:
        continue
    if int(float(row["quantity"])) <= 0:
        continue
    if row["status"] not in valid_status:
        continue
    seen.add(row["order_id"])
    clean_orders.append(row)

conn.executescript("""
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY, date TEXT NOT NULL, year_month TEXT NOT NULL,
    year INTEGER NOT NULL, quarter TEXT NOT NULL, month INTEGER NOT NULL,
    weekday INTEGER NOT NULL, is_weekend INTEGER NOT NULL
);
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY, customer_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL, city TEXT NOT NULL, segment TEXT NOT NULL
);
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY, product_id TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL, category TEXT NOT NULL,
    list_price REAL NOT NULL, cost REAL NOT NULL
);
CREATE TABLE dwd_fact_orders (
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
CREATE INDEX idx_dwd_date ON dwd_fact_orders(date_key);
CREATE INDEX idx_dwd_customer ON dwd_fact_orders(customer_key);
""")
conn.executemany(
    "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    [(int(r["date_id"]), r["date"], r["year_month"], int(r["year"]), r["quarter"], int(r["month"]), int(r["weekday"]), int(r["is_weekend"])) for r in calendar],
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
for order in clean_orders:
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
conn.executemany("INSERT INTO dwd_fact_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", fact_rows)

# DWS：按日期和品类汇总
conn.executescript("""
CREATE TABLE dws_daily_category (
    date_key INTEGER NOT NULL, category TEXT NOT NULL, orders INTEGER NOT NULL,
    units INTEGER NOT NULL, net_amount REAL NOT NULL,
    PRIMARY KEY (date_key, category)
);
""")
conn.execute(
    """
    INSERT INTO dws_daily_category
    SELECT f.date_key, p.category, COUNT(*), SUM(f.quantity), ROUND(SUM(f.net_amount), 2)
    FROM dwd_fact_orders f
    JOIN dim_product p ON p.product_key = f.product_key
    WHERE f.status IN ('completed', 'paid')
    GROUP BY f.date_key, p.category
    """
)

# ADS：月度指标
conn.executescript("""
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
    INSERT INTO ads_monthly_metrics
    SELECT d.year_month,
           ROUND(SUM(CASE WHEN f.status <> 'cancelled' THEN f.gross_amount ELSE 0 END), 2),
           ROUND(SUM(CASE WHEN f.status IN ('completed', 'paid') THEN f.net_amount ELSE 0 END), 2),
           ROUND(SUM(CASE WHEN f.status = 'completed' THEN f.net_amount ELSE 0 END), 2),
           SUM(CASE WHEN f.status IN ('completed', 'paid') THEN 1 ELSE 0 END),
           SUM(CASE WHEN f.status = 'completed' THEN 1 ELSE 0 END)
    FROM dwd_fact_orders f
    JOIN dim_date d ON d.date_key = f.date_key
    GROUP BY d.year_month
    """
)
conn.commit()

print("ODS 订单行数:", conn.execute("SELECT COUNT(*) FROM ods_orders").fetchone()[0])
print("DWD 事实行数:", conn.execute("SELECT COUNT(*) FROM dwd_fact_orders").fetchone()[0])
print("DWS 日品类行数:", conn.execute("SELECT COUNT(*) FROM dws_daily_category").fetchone()[0])
print("ADS 月份数:", conn.execute("SELECT COUNT(*) FROM ads_monthly_metrics").fetchone()[0])


expected_clean = conn.execute("SELECT COUNT(DISTINCT order_id) FROM ods_orders WHERE CAST(quantity AS INTEGER) > 0").fetchone()[0]
checks = [
    ("DWD 事实行数等于清洗后订单数", "SELECT COUNT(*) FROM dwd_fact_orders", expected_clean),
    ("日期维表无孤儿", "SELECT COUNT(*) FROM dwd_fact_orders f LEFT JOIN dim_date d ON d.date_key = f.date_key WHERE d.date_key IS NULL", 0),
    ("客户维表无孤儿", "SELECT COUNT(*) FROM dwd_fact_orders f LEFT JOIN dim_customer c ON c.customer_key = f.customer_key WHERE c.customer_key IS NULL", 0),
    ("商品维表无孤儿", "SELECT COUNT(*) FROM dwd_fact_orders f LEFT JOIN dim_product p ON p.product_key = f.product_key WHERE p.product_key IS NULL", 0),
    ("负金额", "SELECT COUNT(*) FROM dwd_fact_orders WHERE net_amount < 0", 0),
    ("重复订单", "SELECT COUNT(*) FROM (SELECT order_id FROM dwd_fact_orders GROUP BY order_id HAVING COUNT(*) > 1)", 0),
    ("非法状态", "SELECT COUNT(*) FROM dwd_fact_orders WHERE status NOT IN ('completed', 'paid', 'refunded', 'cancelled')", 0),
]
failed = 0
for label, sql, expected in checks:
    actual = conn.execute(sql).fetchone()[0]
    ok = actual == expected
    failed += 0 if ok else 1
    print(("PASS" if ok else "FAIL"), label, "=>", actual)
print()
print("检查通过" if failed == 0 else f"有 {failed} 项未通过")


print("月度指标（最近 6 个月）：")
show(conn.execute("SELECT * FROM ads_monthly_metrics ORDER BY year_month DESC LIMIT 6"))
print()
print("品类贡献：")
show(
    conn.execute(
        """
        SELECT category, net_amount, ROUND(100.0 * net_amount / SUM(net_amount) OVER (), 2) AS share_pct
        FROM (
            SELECT p.category AS category, ROUND(SUM(f.net_amount), 2) AS net_amount
            FROM dwd_fact_orders f
            JOIN dim_product p ON p.product_key = f.product_key
            WHERE f.status IN ('completed', 'paid')
            GROUP BY p.category
        )
        ORDER BY net_amount DESC
        """
    )
)
print()
print("客户排行：")
show(
    conn.execute(
        """
        SELECT c.customer_name, c.city, c.segment, COUNT(*) AS orders, ROUND(SUM(f.net_amount), 2) AS net_amount
        FROM dwd_fact_orders f
        JOIN dim_customer c ON c.customer_key = f.customer_key
        WHERE f.status IN ('completed', 'paid')
        GROUP BY c.customer_name, c.city, c.segment
        ORDER BY net_amount DESC
        LIMIT 5
        """
    )
)
print()
print("渠道结构：")
show(
    conn.execute(
        """
        SELECT channel, COUNT(*) AS orders, ROUND(SUM(net_amount), 2) AS net_amount
        FROM dwd_fact_orders
        WHERE status IN ('completed', 'paid')
        GROUP BY channel
        ORDER BY net_amount DESC
        """
        )
)


monthly_rows = conn.execute(
    "SELECT year_month, gmv, paid_amount, net_revenue, valid_orders, completed_orders FROM ads_monthly_metrics ORDER BY year_month"
).fetchall()
with (out / "monthly_metrics.csv").open("w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["year_month", "gmv", "paid_amount", "net_revenue", "valid_orders", "completed_orders"])
    writer.writerows(monthly_rows)

summary = {
    "rows": {
        "ods_orders": conn.execute("SELECT COUNT(*) FROM ods_orders").fetchone()[0],
        "dwd_orders": conn.execute("SELECT COUNT(*) FROM dwd_fact_orders").fetchone()[0],
        "ads_months": conn.execute("SELECT COUNT(*) FROM ads_monthly_metrics").fetchone()[0],
    },
    "totals": {
        "gmv": conn.execute("SELECT ROUND(SUM(gmv), 2) FROM ads_monthly_metrics").fetchone()[0],
        "paid_amount": conn.execute("SELECT ROUND(SUM(paid_amount), 2) FROM ads_monthly_metrics").fetchone()[0],
        "net_revenue": conn.execute("SELECT ROUND(SUM(net_revenue), 2) FROM ads_monthly_metrics").fetchone()[0],
        "completed_orders": conn.execute("SELECT SUM(completed_orders) FROM ads_monthly_metrics").fetchone()[0],
    },
    "top_category": conn.execute(
        """
        SELECT p.category
        FROM dwd_fact_orders f JOIN dim_product p ON p.product_key = f.product_key
        WHERE f.status IN ('completed', 'paid')
        GROUP BY p.category ORDER BY SUM(f.net_amount) DESC LIMIT 1
        """
    ).fetchone()[0],
    "top_customer": conn.execute(
        """
        SELECT c.customer_name
        FROM dwd_fact_orders f JOIN dim_customer c ON c.customer_key = f.customer_key
        WHERE f.status IN ('completed', 'paid')
        GROUP BY c.customer_name ORDER BY SUM(f.net_amount) DESC LIMIT 1
        """
    ).fetchone()[0],
}
with (out / "metrics.json").open("w", encoding="utf-8") as file:
    json.dump(summary, file, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print()
print("已写入:", out / "monthly_metrics.csv")
print("已写入:", out / "metrics.json")


months = [row[0] for row in monthly_rows]
net_revenue = [row[3] for row in monthly_rows]
category_rows = conn.execute(
    """
    SELECT p.category, ROUND(SUM(f.net_amount), 2) AS net_amount
    FROM dwd_fact_orders f JOIN dim_product p ON p.product_key = f.product_key
    WHERE f.status IN ('completed', 'paid')
    GROUP BY p.category ORDER BY net_amount DESC
    """
).fetchall()
categories = [row[0] for row in category_rows]
category_values = [row[1] for row in category_rows]

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [2.2, 1]})
axes[0].plot(months, net_revenue, marker="o", color="#2563eb", linewidth=2)
axes[0].set_title("月度净收入")
axes[0].set_ylabel("元")
axes[0].tick_params(axis="x", rotation=60)
axes[0].grid(alpha=0.25)

axes[1].barh(categories[::-1], category_values[::-1], color=["#93c5fd", "#86efac", "#fcd34d", "#fca5a5"])
axes[1].set_title("品类贡献")
axes[1].set_xlabel("净额（元）")
for index, value in enumerate(category_values[::-1]):
    axes[1].text(value, index, f" {value:,.0f}", va="center", fontsize=8)

fig.suptitle("销售数仓项目结果", fontsize=14)
fig.tight_layout()
fig.savefig(out / "project-dashboard.png", dpi=130, bbox_inches="tight")
display(Image(filename=str(out / "project-dashboard.png")))
plt.close(fig)
