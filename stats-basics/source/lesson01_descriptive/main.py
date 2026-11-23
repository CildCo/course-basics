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


sales = pd.read_csv(data_path("sales.csv"))
sales["amount"] = sales["units"] * sales["price"]

print("订单数:", len(sales))
print("平均客单价:", round(sales["amount"].mean(), 2))
print("中位数客单价:", round(sales["amount"].median(), 2))
print("两者差值:", round(sales["amount"].mean() - sales["amount"].median(), 2))


quantiles = sales["amount"].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
for level, value in quantiles.items():
    print(f"{level:.0%} 分位: {value:,.2f} 元")

q1 = quantiles.loc[0.25]
q3 = quantiles.loc[0.75]
iqr = q3 - q1
upper = q3 + 1.5 * iqr
print("四分位距 IQR:", round(iqr, 2))
print("超过上界的订单:", int((sales["amount"] > upper).sum()), "笔")
print("金额最高的 5 笔:")
print(sales.nlargest(5, "amount")[["product", "units", "price", "amount"]].to_string(index=False))


by_category = sales.groupby("category")["amount"].agg(["count", "mean", "median"])
by_category["mean_median_gap"] = by_category["mean"] - by_category["median"]
by_category.round(2)
