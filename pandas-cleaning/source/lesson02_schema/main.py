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
raw.columns.tolist()


df = raw.copy()
df.columns = [column.strip().lower().replace(" ", "_") for column in df.columns]
df.columns.tolist()


text_columns = ["order_id", "customer", "region", "category", "product", "status"]
for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

df["units"] = pd.to_numeric(df["units"], errors="coerce").astype("Int64")
df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
df.dtypes


df["amount"] = (df["units"].astype("float") * df["unit_price"]).round(2)
df[["order_id", "units", "unit_price", "amount"]].head()


print("单价范围:", df["unit_price"].min(), "-", df["unit_price"].max())
print("数量缺失:", int(df["units"].isna().sum()))
print("金额合计:", round(float(df["amount"].sum()), 2))
print("列名:", df.columns.tolist())
