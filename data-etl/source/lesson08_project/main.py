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

def extract_orders():
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
    return frame[~invalid].copy(), pd.DataFrame(records).drop_duplicates()

raw = extract_orders()
print("第 1 步 抽取:")
print(raw["source"].value_counts().to_string())
print("合计", len(raw), "行")


dedup = (
    raw.sort_values("updated_at", na_position="first")
    .drop_duplicates("order_id", keep="last")
    .copy()
)
print("第 2 步 去重:", len(raw), "->", len(dedup), "行")

valid, rejected = validate_orders(dedup)
print("第 3 步 校验: 通过", len(valid), "行，拒绝", len(dedup) - len(valid), "行")

report_dir = OUTPUT / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
rejected_path = report_dir / "rejected_orders.csv"
rejected.to_csv(rejected_path, index=False)
print("错误报告:", rejected_path.relative_to(Path.cwd()).as_posix())
print(rejected["reason"].value_counts().to_string())


products = pd.read_csv(data_path("raw/products.csv"))
customers = pd.read_json(data_path("raw/customers.json"), orient="records")

clean = valid.merge(
    products[["product_id", "product_name", "category"]], on="product_id", how="left"
)
clean = clean.merge(
    customers[["customer_id", "city", "segment"]], on="customer_id", how="left"
)
clean["amount"] = (clean["qty"].astype("float") * clean["unit_price"]).round(2)

db_path = OUTPUT / "warehouse.db"
rows = [
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
    for row in clean.itertuples(index=False)
]

with sqlite3.connect(db_path) as conn:
    conn.execute("DROP TABLE IF EXISTS orders_clean")
    conn.execute(
        """
        CREATE TABLE orders_clean (
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
        "INSERT OR REPLACE INTO orders_clean VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    loaded_count = conn.execute("SELECT COUNT(*) FROM orders_clean").fetchone()[0]

summary = (
    clean.groupby("category")
    .agg(
        order_count=("order_id", "count"),
        revenue=("amount", "sum"),
        avg_amount=("amount", "mean"),
    )
    .sort_values("revenue", ascending=False)
    .round(2)
)
summary_path = report_dir / "summary.csv"
summary.to_csv(summary_path)

print("第 4 步 写入 SQLite:", loaded_count, "行 ->", db_path.name)
print("第 5 步 分类汇总:")
print(summary.to_string())
print("汇总文件:", summary_path.relative_to(Path.cwd()).as_posix())

top_category = summary.index[0]
reject_rate = (len(dedup) - len(valid)) / len(dedup) * 100
print(
    f"结论：有效订单 {len(clean)} 笔，销售额 {clean['amount'].sum():,.2f} 元，"
    f"{top_category} 类贡献最高；拒绝率 {reject_rate:.1f}%。"
)
