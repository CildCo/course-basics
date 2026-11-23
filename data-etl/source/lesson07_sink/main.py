import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)
print("pandas", pd.__version__)
print("工作目录就绪")


def load_orders():
    jan = pd.read_csv(data_path("raw/orders-2026-01.csv"))
    feb = pd.read_csv(data_path("raw/orders-2026-02.csv"))
    feb = feb.rename(columns={"quantity": "qty", "price": "unit_price"})
    jan["source"] = "orders-2026-01.csv"
    feb["source"] = "orders-2026-02.csv"

    frame = pd.concat([jan, feb], ignore_index=True)
    frame["customer_id"] = frame["customer_id"].astype("string").str.strip()
    frame["product_id"] = frame["product_id"].astype("string").str.strip()
    frame["status"] = frame["status"].astype("string").str.lower().str.strip()
    frame["qty"] = pd.to_numeric(frame["qty"], errors="coerce").astype("Int64")
    frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="coerce")
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    frame["updated_at"] = pd.to_datetime(frame["updated_at"], errors="coerce")
    return frame

def clean_orders():
    orders = load_orders()
    orders = (
        orders.sort_values("updated_at", na_position="first")
        .drop_duplicates("order_id", keep="last")
    )
    status_values = {"paid", "shipped", "completed", "cancelled", "refunded"}
    mask = (
        orders["customer_id"].notna()
        & orders["product_id"].notna()
        & orders["status"].isin(status_values)
        & orders["qty"].notna()
        & orders["qty"].between(1, 20)
        & orders["unit_price"].notna()
        & orders["unit_price"].between(0.01, 2000)
        & orders["order_date"].notna()
        & orders["updated_at"].notna()
    )
    return orders[mask].copy()

clean = clean_orders()
print("清洗后订单:", len(clean), "行")
print("主键唯一:", clean["order_id"].is_unique)
clean.head(3)


import sqlite3

db_path = OUTPUT / "warehouse.db"
rows = []
for row in clean.itertuples(index=False):
    rows.append(
        (
            str(row.order_id),
            str(row.customer_id),
            str(row.product_id),
            int(row.qty),
            float(row.unit_price),
            row.order_date.strftime("%Y-%m-%d"),
            str(row.status),
            row.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
    )

with sqlite3.connect(db_path) as conn:
    conn.execute("DROP TABLE IF EXISTS orders")
    conn.execute(
        """
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

print("写入", len(rows), "行到", db_path.name)


with sqlite3.connect(db_path) as conn:
    total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    unique_keys = conn.execute("SELECT COUNT(DISTINCT order_id) FROM orders").fetchone()[0]
    duplicates = conn.execute(
        "SELECT order_id FROM orders GROUP BY order_id HAVING COUNT(*) > 1"
    ).fetchall()
    total_amount = conn.execute("SELECT ROUND(SUM(qty * unit_price), 2) FROM orders").fetchone()[0]

print("表内行数:", total)
print("不同主键:", unique_keys)
print("重复主键:", duplicates)
print("订单金额合计:", total_amount)


partition_dir = OUTPUT / "partitions"
partition_dir.mkdir(parents=True, exist_ok=True)
for period, part in clean.groupby(clean["order_date"].dt.to_period("M")):
    path = partition_dir / f"orders-{period}.csv"
    part.to_csv(path, index=False)
    print(f"{path.name}: {len(part)} 行")

print("分区文件:", sorted(path.name for path in partition_dir.glob("*.csv")))


with sqlite3.connect(db_path) as conn:
    loaded = pd.read_sql_query("SELECT * FROM orders ORDER BY order_id", conn)

print("回读行数:", len(loaded))
print("内存行数:", len(clean))
print("主键唯一:", loaded["order_id"].is_unique)
print("首行订单:", loaded.iloc[0]["order_id"], loaded.iloc[0]["status"])
loaded.head(3)
