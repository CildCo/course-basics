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
    return frame

orders = load_orders()
print("原始订单:", len(orders), "行")
print("字段:", list(orders.columns))


mapping = {
    "quantity": "qty",
    "price": "unit_price",
}

mapping_table = pd.DataFrame(
    [{"源字段": key, "标准字段": value} for key, value in mapping.items()]
)
print("本次字段映射:")
print(mapping_table.to_string(index=False))


clean = orders.copy()
clean["order_id"] = clean["order_id"].astype("string").str.strip()
clean["customer_id"] = clean["customer_id"].astype("string").str.strip()
clean["product_id"] = clean["product_id"].astype("string").str.strip()
clean["status"] = clean["status"].astype("string").str.lower().str.strip()
clean["qty"] = pd.to_numeric(clean["qty"], errors="coerce").astype("Int64")
clean["unit_price"] = pd.to_numeric(clean["unit_price"], errors="coerce")
clean["order_date"] = pd.to_datetime(clean["order_date"], errors="coerce")
clean["updated_at"] = pd.to_datetime(clean["updated_at"], errors="coerce")

print(clean.dtypes.to_string())
print("日期解析失败:", int(clean["order_date"].isna().sum()), "行")
print("金额解析失败:", int(clean["unit_price"].isna().sum()), "行")


bad_dates = clean[clean["order_date"].isna() | clean["updated_at"].isna()]
print("日期有问题的行:", len(bad_dates))
print(bad_dates[["order_id", "order_date", "updated_at"]].to_string(index=False))

clean["order_month"] = clean["order_date"].dt.to_period("M").astype("string")
print("订单月份分布:")
print(clean["order_month"].value_counts(dropna=False).to_string())
clean[["order_id", "qty", "unit_price", "order_date", "order_month"]].head()
