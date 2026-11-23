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

orders = load_orders()
before = len(orders)
dedup = (
    orders.sort_values("updated_at", na_position="first")
    .drop_duplicates("order_id", keep="last")
    .copy()
)
print("原始", before, "行，去重后", len(dedup), "行，移除", before - len(dedup), "行")
print("主键是否唯一:", dedup["order_id"].is_unique)
dedup[["order_id", "status", "updated_at"]].sort_values("updated_at").tail(5)


clean = dedup[dedup["updated_at"].notna()].copy()
watermark = pd.Timestamp("2026-01-31 23:59:59")
initial = clean[clean["updated_at"] <= watermark]
batch = clean[clean["updated_at"] > watermark]

def to_record(row):
    return {
        "order_id": row.order_id,
        "customer_id": row.customer_id,
        "product_id": row.product_id,
        "qty": row.qty,
        "unit_price": row.unit_price,
        "order_date": row.order_date,
        "status": row.status,
        "updated_at": row.updated_at,
    }

def incremental_load(store, rows, last_watermark):
    todo = rows[rows["updated_at"] > last_watermark].sort_values("updated_at")
    inserted = 0
    for row in todo.itertuples(index=False):
        store[row.order_id] = to_record(row)
        inserted += 1
    new_watermark = todo["updated_at"].max() if len(todo) else last_watermark
    return inserted, new_watermark

store = {}
for row in initial.itertuples(index=False):
    store[row.order_id] = to_record(row)
print("首次载入一月订单:", len(store), "笔")

inserted_first, watermark_after = incremental_load(store, batch, watermark)
print("第二次运行处理:", inserted_first, "笔，新水位线:", watermark_after)
size_after_first = len(store)

inserted_second, _ = incremental_load(store, batch, watermark_after)
print("第三次运行处理:", inserted_second, "笔")
print("两次运行后的行数一致:", size_after_first == len(store))


import hashlib

loaded = pd.DataFrame(store.values()).sort_values("order_id")
out_dir = OUTPUT / "incremental"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "orders_loaded.csv"

loaded.to_csv(out_path, index=False)
first_hash = hashlib.md5(out_path.read_bytes()).hexdigest()
loaded.to_csv(out_path, index=False)
second_hash = hashlib.md5(out_path.read_bytes()).hexdigest()

print("已加载订单:", len(loaded), "行")
print("第一次输出哈希:", first_hash)
print("第二次输出哈希:", second_hash)
print("两次输出哈希一致:", first_hash == second_hash)
