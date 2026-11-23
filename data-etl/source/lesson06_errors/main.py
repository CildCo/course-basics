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

orders = load_orders()
valid, rejected = validate_orders(orders)
print("总行数:", len(orders))
print("通过:", len(valid), "行")
print("隔离:", len(orders) - len(valid), "行")
print("错误记录:", len(rejected), "条")


report_dir = OUTPUT / "errors"
report_dir.mkdir(parents=True, exist_ok=True)
report_path = report_dir / "rejected_orders.csv"
rejected.to_csv(report_path, index=False)

print("错误报告:", report_path.relative_to(Path.cwd()).as_posix())
print("按原因统计:")
print(rejected["reason"].value_counts().to_string())
print("按来源统计:")
print(rejected["source"].value_counts().to_string())
rejected.head(8)


attempts = []

def load_batch(rows, fail_first=2):
    attempts.append(len(attempts) + 1)
    if len(attempts) <= fail_first:
        raise RuntimeError("目标表暂时不可写")
    return len(rows)

def load_with_retry(rows, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            loaded = load_batch(rows)
            print(f"第 {attempt} 次尝试成功，写入 {loaded} 行")
            return loaded
        except RuntimeError as exc:
            print(f"第 {attempt} 次尝试失败：{exc}")
    raise RuntimeError("超过最大重试次数")

attempts.clear()
loaded = load_with_retry(valid)
print("累计尝试次数:", len(attempts))
