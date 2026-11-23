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


orders_jan = pd.read_csv(data_path("raw/orders-2026-01.csv"))
orders_feb = pd.read_csv(data_path("raw/orders-2026-02.csv"))
customers = pd.read_json(data_path("raw/customers.json"), orient="records")
products = pd.read_csv(data_path("raw/products.csv"))

for name, frame in [
    ("一月订单", orders_jan),
    ("二月订单", orders_feb),
    ("客户", customers),
    ("商品", products),
]:
    print(f"{name}: {len(frame)} 行 x {len(frame.columns)} 列")

print("一月字段:", list(orders_jan.columns))
print("二月字段:", list(orders_feb.columns))
print("仅一侧存在的字段:", sorted(set(orders_jan.columns) ^ set(orders_feb.columns)))


def normalize(frame, source):
    frame = frame.rename(columns={"quantity": "qty", "price": "unit_price"}).copy()
    frame["source"] = source
    columns = [
        "order_id", "customer_id", "product_id", "qty", "unit_price",
        "order_date", "status", "updated_at", "source",
    ]
    return frame[columns]

orders = pd.concat(
    [
        normalize(orders_jan, "orders-2026-01.csv"),
        normalize(orders_feb, "orders-2026-02.csv"),
    ],
    ignore_index=True,
)
print(orders["source"].value_counts().to_string())
print("合并后:", len(orders), "行")
orders.head(3)
