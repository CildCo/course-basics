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
orders = read_csv("orders.csv")

conn = sqlite3.connect(":memory:")
conn.executescript("""
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    year_month TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL
);
CREATE TABLE fact_orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    date_key INTEGER NOT NULL,
    status TEXT NOT NULL,
    gross_amount REAL NOT NULL,
    net_amount REAL NOT NULL
);
""")
conn.executemany(
    "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?)",
    [(int(r["date_id"]), r["date"], r["year_month"], int(r["year"]), int(r["month"])) for r in calendar],
)
fact_rows = []
for order in orders:
    gross = round(int(order["quantity"]) * float(order["unit_price"]), 2)
    fact_rows.append(
        (
            order["order_id"],
            order["order_date"],
            int(order["order_date"].replace("-", "")),
            order["status"],
            gross,
            round(gross - float(order["discount_amount"]), 2),
        )
    )
conn.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?)", fact_rows)
conn.commit()
print("事实行数:", conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0])
show(conn.execute("SELECT status, COUNT(*) AS orders FROM fact_orders GROUP BY status ORDER BY orders DESC"))


month_start = "2026-06-01"
month_end = "2026-07-01"

metrics = [
    (
        "GMV 下单金额",
        "非取消订单的吊牌金额",
        "SELECT ROUND(SUM(gross_amount), 2) FROM fact_orders WHERE status <> 'cancelled' AND order_date >= ? AND order_date < ?",
    ),
    (
        "支付金额",
        "已完成或已支付订单的实付金额",
        "SELECT ROUND(SUM(net_amount), 2) FROM fact_orders WHERE status IN ('completed', 'paid') AND order_date >= ? AND order_date < ?",
    ),
    (
        "净收入",
        "仅已完成订单的实付金额",
        "SELECT ROUND(SUM(net_amount), 2) FROM fact_orders WHERE status = 'completed' AND order_date >= ? AND order_date < ?",
    ),
]
values = []
for name, note, sql in metrics:
    value = conn.execute(sql, (month_start, month_end)).fetchone()[0] or 0.0
    values.append(value)
    print(f"{name}: {value:,.2f}  ({note})")
print()
print(f"最高与最低口径相差: {max(values) - min(values):,.2f}")


counts = [
    ("全部订单", "包含取消订单", "SELECT COUNT(*) FROM fact_orders WHERE order_date >= ? AND order_date < ?"),
    ("非取消订单", "status <> 'cancelled'", "SELECT COUNT(*) FROM fact_orders WHERE status <> 'cancelled' AND order_date >= ? AND order_date < ?"),
    ("有效订单", "completed 或 paid", "SELECT COUNT(*) FROM fact_orders WHERE status IN ('completed', 'paid') AND order_date >= ? AND order_date < ?"),
    ("成交订单", "仅 completed", "SELECT COUNT(*) FROM fact_orders WHERE status = 'completed' AND order_date >= ? AND order_date < ?"),
]
for name, note, sql in counts:
    print(f"{name}: {conn.execute(sql, (month_start, month_end)).fetchone()[0]} 笔  ({note})")


sql = """
SELECT d.year_month,
       ROUND(SUM(CASE WHEN f.status <> 'cancelled' THEN f.gross_amount ELSE 0 END), 2) AS gmv,
       ROUND(SUM(CASE WHEN f.status IN ('completed', 'paid') THEN f.net_amount ELSE 0 END), 2) AS paid_amount,
       ROUND(SUM(CASE WHEN f.status = 'completed' THEN f.net_amount ELSE 0 END), 2) AS net_revenue
FROM fact_orders f
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month
ORDER BY d.year_month
"""
rows = conn.execute(sql).fetchall()
months = [row[0] for row in rows]
gmv = [row[1] for row in rows]
paid = [row[2] for row in rows]
net = [row[3] for row in rows]

fig, ax = plt.subplots(figsize=(11, 4.8))
ax.plot(months, gmv, marker="o", linewidth=2, label="GMV 下单金额", color="#2563eb")
ax.plot(months, paid, marker="s", linewidth=2, label="支付金额", color="#16a34a")
ax.plot(months, net, marker="^", linewidth=2, label="净收入", color="#d97706")
ax.set_title("同一份订单，三种销售额口径")
ax.set_ylabel("金额（元）")
ax.tick_params(axis="x", rotation=60)
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(out / "metric-trend.png", dpi=130, bbox_inches="tight")
display(Image(filename=str(out / "metric-trend.png")))
plt.close(fig)
