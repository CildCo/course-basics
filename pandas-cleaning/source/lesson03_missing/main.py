from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import pandas as pd

raw = pd.read_csv(data_path("orders_dirty.csv"), dtype={"order_id": "string"})
missing = pd.DataFrame({
    "缺失数": raw.isna().sum(),
    "缺失比例": raw.isna().mean().round(3),
})
missing[missing["缺失数"] > 0]


df = raw.copy()
df["customer"] = df["customer"].fillna("未知客户")
df["region"] = df["region"].fillna("未知")
df["status"] = df["status"].fillna("未知")
df.isna().sum()


missing_price = df["unit_price"].isna()
median_by_category = df.groupby("category")["unit_price"].transform("median")
df["unit_price"] = df["unit_price"].fillna(median_by_category)

print("单价缺失修正:", int(missing_price.sum()))
print("修正后的单价:", sorted(df.loc[missing_price, "unit_price"].unique()))
print("剩余缺失:", int(df["unit_price"].isna().sum()))


before = len(df)
df_valid = df.dropna(subset=["order_date"])
print("因日期缺失删除:", before - len(df_valid), "行")
print("剩余行数:", len(df_valid))
print("日期缺失行:")
df[df["order_date"].isna()][["order_id", "order_date", "customer"]]
