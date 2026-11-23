from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import numpy as np
import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

orders = pd.read_csv(
    data_path("orders.csv"),
    dtype={"customer_id": "string", "product_id": "string", "order_date": "string"},
)
customers = pd.read_csv(data_path("customers.csv"), dtype="string")
products = pd.read_csv(data_path("products.csv"), dtype="string")

orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="coerce")
orders["amount"] = pd.to_numeric(orders["amount"], errors="coerce")

print("订单表:", orders.shape)
print("客户表:", customers.shape)
print("商品表:", products.shape)
print(orders.head(3).to_string(index=False))


as_of = pd.Timestamp("2026-10-01")
order_dates = pd.to_datetime(orders["order_date"], errors="coerce", format="mixed")

checks = [
    ["完整性", "客户号、日期、状态都不为空", int(orders[["customer_id", "order_date", "status"]].isna().any(axis=1).sum())],
    ["唯一性", "订单号不重复", int(orders["order_id"].duplicated().sum())],
    ["范围", "数量在 1 到 99 之间", int((~orders["quantity"].between(1, 99)).sum())],
    ["一致性", "金额等于数量乘单价", int(((orders["amount"] - (orders["quantity"] * orders["unit_price"]).round(2)).abs() > 0.01).sum())],
    ["及时性", "日期不晚于统计日", int((order_dates > as_of).sum())],
]
overview = pd.DataFrame(checks, columns=["维度", "检查", "异常行数"])
print(overview.to_string(index=False))
print()
print("异常行数合计:", int(overview["异常行数"].sum()))


dup = orders[orders["order_id"].duplicated(keep=False)].sort_values(["order_id", "amount"])
print("重复订单号:", dup["order_id"].nunique(), "个；涉及", len(dup), "行")
print(dup[["order_id", "customer_id", "product_id", "order_date", "quantity", "amount"]].head(8).to_string(index=False))


for name, frame in [("orders", orders), ("customers", customers), ("products", products)]:
    gaps = frame.isna().sum()
    gaps = gaps[gaps > 0]
    print(name, "缺失列:", {column: int(count) for column, count in gaps.items()})
