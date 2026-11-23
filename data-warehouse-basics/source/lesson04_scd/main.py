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
changes = read_csv("customer_changes.csv")
orders = read_csv("orders.csv")

changes_by_customer = {}
for row in changes:
    changes_by_customer.setdefault(row["customer_id"], []).append(row)

versions = []
for customer in customers:
    customer_id = customer["customer_id"]
    history = [(customer["signup_date"], customer["city"], customer["segment"])]
    for event in sorted(changes_by_customer.get(customer_id, []), key=lambda r: r["change_date"]):
        if (event["city"], event["segment"]) != (history[-1][1], history[-1][2]):
            history.append((event["change_date"], event["city"], event["segment"]))
    for index, (valid_from, city, segment) in enumerate(history):
        valid_to = history[index + 1][0] if index + 1 < len(history) else "9999-12-31"
        versions.append(
            (
                len(versions) + 1,
                customer_id,
                customer["customer_name"],
                city,
                segment,
                valid_from,
                valid_to,
                1 if index + 1 == len(history) else 0,
            )
        )

conn = sqlite3.connect(":memory:")
conn.executescript("""
CREATE TABLE dim_customer_scd (
    customer_sk INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    segment TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    is_current INTEGER NOT NULL
);
CREATE TABLE fact_orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    net_amount REAL NOT NULL,
    status TEXT NOT NULL
);
""")
conn.executemany("INSERT INTO dim_customer_scd VALUES (?, ?, ?, ?, ?, ?, ?, ?)", versions)
fact_rows = []
for order in orders:
    gross = round(int(order["quantity"]) * float(order["unit_price"]), 2)
    fact_rows.append(
        (
            order["order_id"],
            order["order_date"],
            order["customer_id"],
            order["product_id"],
            round(gross - float(order["discount_amount"]), 2),
            order["status"],
        )
    )
conn.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?)", fact_rows)
conn.commit()

print("客户实体数:", conn.execute("SELECT COUNT(DISTINCT customer_id) FROM dim_customer_scd").fetchone()[0])
print("维表版本数:", conn.execute("SELECT COUNT(*) FROM dim_customer_scd").fetchone()[0])
print("发生过变化的客户:", conn.execute("SELECT COUNT(*) FROM (SELECT customer_id FROM dim_customer_scd GROUP BY customer_id HAVING COUNT(*) > 1)").fetchone()[0])
changed_id = conn.execute("SELECT customer_id FROM dim_customer_scd GROUP BY customer_id HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC LIMIT 1").fetchone()[0]
print("示例客户:", changed_id)
show(conn.execute("SELECT customer_id, city, segment, valid_from, valid_to, is_current FROM dim_customer_scd WHERE customer_id = ? ORDER BY valid_from", (changed_id,)))


history_sql = """
SELECT s.segment,
       COUNT(DISTINCT f.order_id) AS orders,
       ROUND(SUM(f.net_amount), 2) AS net_amount
FROM fact_orders f
JOIN dim_customer_scd s
  ON s.customer_id = f.customer_id
 AND f.order_date >= s.valid_from
 AND f.order_date < s.valid_to
WHERE f.status IN ('completed', 'paid')
GROUP BY s.segment
ORDER BY net_amount DESC
"""
current_sql = """
SELECT s.segment,
       COUNT(DISTINCT f.order_id) AS orders,
       ROUND(SUM(f.net_amount), 2) AS net_amount
FROM fact_orders f
JOIN dim_customer_scd s
  ON s.customer_id = f.customer_id
 AND s.is_current = 1
WHERE f.status IN ('completed', 'paid')
GROUP BY s.segment
ORDER BY net_amount DESC
"""
print("按订单发生时的客户等级：")
show(conn.execute(history_sql))
print()
print("按客户当前等级：")
show(conn.execute(current_sql))


show(
    conn.execute(
        """
        SELECT s.valid_from,
               s.valid_to,
               s.city,
               s.segment,
               COUNT(f.order_id) AS orders,
               ROUND(COALESCE(SUM(f.net_amount), 0), 2) AS net_amount
        FROM dim_customer_scd s
        LEFT JOIN fact_orders f
          ON f.customer_id = s.customer_id
         AND f.order_date >= s.valid_from
         AND f.order_date < s.valid_to
         AND f.status IN ('completed', 'paid')
        WHERE s.customer_id = ?
        GROUP BY s.customer_sk
        ORDER BY s.valid_from
        """,
        (changed_id,),
    )
)
