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
print("订单表:", orders.shape, "客户表:", customers.shape, "商品表:", products.shape)


def missing_detail(frame, columns):
    rows = []
    for column in columns:
        mask = frame[column].isna()
        if mask.any():
            sample = ", ".join(frame.index[mask].astype(str)[:5])
            rows.append({"column": column, "missing": int(mask.sum()), "first_rows": sample})
    return pd.DataFrame(rows)


print("订单表缺失明细")
print(missing_detail(orders, orders.columns).to_string(index=False))
print()
print("客户表缺失明细")
print(missing_detail(customers, customers.columns).to_string(index=False))


exact = orders[orders.duplicated(keep=False)]
by_id = orders[orders["order_id"].duplicated(keep=False)]

print("完全重复：多出", int(orders.duplicated().sum()), "行；涉及", len(exact), "行")
print("订单号重复：多出", int(orders["order_id"].duplicated().sum()), "行；涉及", len(by_id), "行")
print()
print(by_id.sort_values("order_id").head(8).to_string(index=False))


step1 = orders.drop_duplicates()
step2 = step1.drop_duplicates(subset="order_id", keep="last").copy()

print("原始行数:", len(orders))
print("删除完全重复后:", len(step1))
print("处理主键重复后:", len(step2))
print("order_id 仍重复:", int(step2["order_id"].duplicated().sum()))


def pk_report(frame, key, label):
    return {
        "表": label,
        "行数": len(frame),
        "唯一键数": int(frame[key].nunique(dropna=False)),
        "重复键数": int(frame[key].duplicated().sum()),
    }


pk = pd.DataFrame(
    [
        pk_report(orders, "order_id", "订单表"),
        pk_report(customers, "customer_id", "客户表"),
        pk_report(products, "product_id", "商品表"),
    ]
)
print(pk.to_string(index=False))
print()
print(customers.loc[customers["customer_id"] == "C003", ["customer_id", "name", "region", "level", "signup_date"]].to_string(index=False))
print(products.loc[products["product_id"] == "P008", ["product_id", "name", "category", "unit_price", "is_active"]].to_string(index=False))
