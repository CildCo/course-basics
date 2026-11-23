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
print("待校验订单:", len(orders), "行")


def validate_orders(frame):
    status_values = {"paid", "shipped", "completed", "cancelled", "refunded"}
    checks = {
        "主键重复": frame["order_id"].duplicated(keep=False),
        "客户为空": frame["customer_id"].isna(),
        "商品为空": frame["product_id"].isna(),
        "状态非法": ~frame["status"].isin(status_values),
        "数量为空": frame["qty"].isna(),
        "数量越界": frame["qty"].notna() & ~frame["qty"].between(1, 20),
        "金额为空": frame["unit_price"].isna(),
        "金额越界": frame["unit_price"].notna() & ~frame["unit_price"].between(0.01, 2000),
        "下单日期非法": frame["order_date"].isna(),
        "更新时间非法": frame["updated_at"].isna(),
    }

    invalid = pd.Series(False, index=frame.index)
    records = []
    for reason, mask in checks.items():
        invalid |= mask
        for idx in frame.index[mask]:
            row = frame.loc[idx]
            records.append(
                {
                    "order_id": str(row["order_id"]),
                    "source": str(row["source"]),
                    "reason": reason,
                }
            )
    errors = pd.DataFrame(records).drop_duplicates()
    return frame[~invalid].copy(), errors

valid, errors = validate_orders(orders)
print("错误类型统计:")
print(errors["reason"].value_counts().to_string())
print("涉及订单:", errors["order_id"].nunique(), "个")
print("通过校验:", len(valid), "行")
print("未通过校验:", len(orders) - len(valid), "行")
errors.head(10)


error_dir = OUTPUT / "validation"
error_dir.mkdir(parents=True, exist_ok=True)
error_path = error_dir / "errors.csv"
errors.to_csv(error_path, index=False)

print("错误明细已写入:", error_path.relative_to(Path.cwd()).as_posix())
print("按来源统计:")
print(errors.groupby(["source", "reason"]).size().to_string())
