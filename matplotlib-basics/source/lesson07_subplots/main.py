import matplotlib
matplotlib.use("Agg")

from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False


import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(data_path("sales.csv"))
df["date"] = pd.to_datetime(df["date"])
df["amount"] = df["units"] * df["price"]
category = df.groupby("category")["amount"].sum().sort_values()
monthly = df.assign(month=df["date"].dt.to_period("M")).groupby("month")["amount"].sum()


fig, axes = plt.subplots(2, 2, figsize=(8, 6))
axes[0, 0].bar(category.index, category.values, color="#4f7cff")
axes[0, 0].set_title("分类销售额")
axes[0, 1].plot(monthly.index.astype(str), monthly.values, marker="o", color="#2f8f5b")
axes[0, 1].set_title("月度销售额")
axes[1, 0].scatter(df["units"], df["amount"], alpha=0.6, color="#d97706")
axes[1, 0].set_title("数量与销售额")
axes[1, 1].hist(df["amount"], bins=8, color="#7c5cfc")
axes[1, 1].set_title("销售额分布")
fig.suptitle("销售数据一页概览")
plt.tight_layout()
