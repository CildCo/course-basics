from pathlib import Path

import time

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

rng = np.random.default_rng(42)
n = 50000
big = pd.DataFrame({
    "order_id": np.arange(n),
    "city": rng.choice(["北京", "上海", "广州", "深圳", "杭州", "成都"], size=n),
    "channel": rng.choice(["线上", "门店"], size=n),
    "quantity": rng.integers(1, 8, size=n),
    "unit_price": rng.choice([89.0, 159.0, 199.0, 299.0, 399.0, 549.0], size=n),
})
big["revenue"] = big["quantity"] * big["unit_price"]

print("数据量:", big.shape)
print("原始内存 MB:", round(big.memory_usage(deep=True).sum() / 1024 ** 2, 2))
print(big.head(3).to_string(index=False))


optimized = big.copy()
optimized["city"] = optimized["city"].astype("category")
optimized["channel"] = optimized["channel"].astype("category")
optimized["quantity"] = optimized["quantity"].astype("int16")
optimized["unit_price"] = optimized["unit_price"].astype("float32")

print(optimized.dtypes.to_string())
for column in ["city", "channel"]:
    before = int(big[column].memory_usage(deep=True))
    after = int(optimized[column].memory_usage(deep=True))
    print(f"{column}: {before} -> {after} 字节")

print("优化后内存 MB:", round(optimized.memory_usage(deep=True).sum() / 1024 ** 2, 2))


def price_tier(price):
    if price >= 500:
        return "高客单"
    if price >= 200:
        return "中客单"
    return "低客单"


start = time.perf_counter()
by_apply = big["unit_price"].apply(price_tier)
apply_seconds = time.perf_counter() - start

start = time.perf_counter()
by_cut = pd.cut(
    big["unit_price"],
    bins=[0, 200, 500, float("inf")],
    labels=["低客单", "中客单", "高客单"],
    right=False,
)
cut_seconds = time.perf_counter() - start

print("apply 用时（秒）:", round(apply_seconds, 4))
print("cut 用时（秒）:", round(cut_seconds, 4))
print("结果一致:", bool((by_apply == by_cut.astype(str)).all()))
print(by_apply.value_counts().sort_index().to_string())


big["is_online"] = np.where(big["channel"] == "线上", "是", "否")
print(big["is_online"].value_counts().to_string())
print("销售额校验:", round(float(big["revenue"].sum()), 2))


big.to_csv(out / "big_orders.csv", index=False)

rows = 0
total = 0.0
chunks = 0
for chunk in pd.read_csv(out / "big_orders.csv", usecols=["quantity", "revenue"], chunksize=10000):
    rows += len(chunk)
    total += float(chunk["revenue"].sum())
    chunks += 1

print("分块数:", chunks, "行数:", rows)
print("分块合计:", round(total, 2))
print("整表合计:", round(float(big["revenue"].sum()), 2))
