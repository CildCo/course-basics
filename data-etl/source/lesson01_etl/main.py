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


raw_orders = [
    {"order_id": "A001", "amount": "128.00", "status": "PAID"},
    {"order_id": "A002", "amount": "89.50", "status": "paid"},
    {"order_id": "A003", "amount": "399.00", "status": "Shipped"},
]

def extract(rows):
    return [dict(row) for row in rows]

def transform(rows):
    return [
        {
            "order_id": row["order_id"],
            "amount": float(row["amount"]),
            "status": row["status"].lower(),
        }
        for row in rows
    ]

def load(rows, store):
    for row in rows:
        store[row["order_id"]] = row
    return store

store = {}
load(transform(extract(raw_orders)), store)
print("第一次加载:", len(store), "笔")
print(store["A001"])


out_dir = OUTPUT / "intro"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "orders.csv"

def run_pipeline():
    rows = transform(extract(raw_orders))
    pd.DataFrame(rows).sort_values("order_id").to_csv(out_file, index=False)
    return pd.read_csv(out_file)

first_run = run_pipeline()
second_run = run_pipeline()
print("第一次行数:", len(first_run))
print("第二次行数:", len(second_run))
print("两次内容一致:", first_run.equals(second_run))
print("结果文件:", out_file.relative_to(Path.cwd()).as_posix())
