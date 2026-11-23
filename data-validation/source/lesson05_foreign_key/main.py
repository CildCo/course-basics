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


def foreign_key_check(fact, fact_key, dim, dim_key):
    missing = fact[fact_key].isna()
    orphan = ~missing & ~fact[fact_key].isin(dim[dim_key])
    return pd.DataFrame(
        [
            {"检查": f"{fact_key} 非空", "异常行": int(missing.sum())},
            {"检查": f"{fact_key} 能匹配 {dim_key}", "异常行": int(orphan.sum())},
        ]
    )


print("客户外键")
print(foreign_key_check(orders, "customer_id", customers, "customer_id").to_string(index=False))
print()
print("商品外键")
print(foreign_key_check(orders, "product_id", products, "product_id").to_string(index=False))


expected = (orders["quantity"] * orders["unit_price"]).round(2)
diff = (orders["amount"] - expected).abs()
bad_amount = orders[diff > 0.01].copy()
bad_amount["expected"] = expected[diff > 0.01]
bad_amount["diff"] = (bad_amount["amount"] - bad_amount["expected"]).round(2)

print("金额不一致:", len(bad_amount), "行")
print(bad_amount[["order_id", "quantity", "unit_price", "amount", "expected", "diff"]].head(8).to_string(index=False))


price_ref = products.drop_duplicates("product_id", keep="first").copy()
price_ref["unit_price"] = pd.to_numeric(price_ref["unit_price"], errors="coerce")
valid_ref = price_ref[(price_ref["unit_price"] > 0) & price_ref["unit_price"].notna()]

merged = orders.merge(
    valid_ref[["product_id", "unit_price"]],
    on="product_id",
    how="left",
    suffixes=("", "_ref"),
)
bad_price = merged[
    merged["unit_price_ref"].notna()
    & ((merged["unit_price"] - merged["unit_price_ref"]).abs() > 0.01)
]
print("单价与商品表不一致:", len(bad_price), "行")
print(bad_price[["order_id", "product_id", "unit_price", "unit_price_ref"]].head(8).to_string(index=False))
