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


raw[["units", "unit_price"]].describe().round(2)


q1, q3 = raw["unit_price"].quantile([0.25, 0.75])
iqr = q3 - q1
upper = q3 + 1.5 * iqr
print("Q1:", q1, "Q3:", q3, "IQR:", iqr)
print("上界:", round(upper, 2))
print("超过上界的行:", int((raw["unit_price"] > upper).sum()))


df = raw.copy()
df["bad_units"] = (df["units"] <= 0) | (df["units"] > 100)
df["bad_price"] = (df["unit_price"] <= 0) | (df["unit_price"] > 5000)
print("无效数量:", int(df["bad_units"].sum()))
print("异常单价:", int(df["bad_price"].sum()))
df[df["bad_units"] | df["bad_price"]][["order_id", "units", "unit_price"]].head(12)


clean = df[~df["bad_units"]].copy()
print("删除无效数量行:", len(df) - len(clean))

valid_median = clean.loc[~clean["bad_price"]].groupby("category")["unit_price"].median()
clean.loc[clean["bad_price"], "unit_price"] = clean.loc[clean["bad_price"], "category"].map(valid_median)
clean["unit_price"] = clean["unit_price"].fillna(clean["unit_price"].median())
print("修正后异常单价:", int(((clean["unit_price"] <= 0) | (clean["unit_price"] > 5000)).sum()))
clean[["units", "unit_price"]].describe().round(2)
