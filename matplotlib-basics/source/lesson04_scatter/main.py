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
df["amount"] = df["units"] * df["price"]
df[["units", "price", "amount"]].head()


fig, ax = plt.subplots(figsize=(6, 3.5))
ax.scatter(df["units"], df["amount"], s=df["price"] * 2, alpha=0.7, color="#4f7cff")
ax.set_title("数量与销售额")
ax.set_xlabel("数量")
ax.set_ylabel("销售额")
plt.tight_layout()


colors = {"办公": "#4f7cff", "数码": "#2f8f5b", "家居": "#d97706"}
fig, ax = plt.subplots(figsize=(6, 3.5))
for name, group in df.groupby("category"):
    ax.scatter(group["units"], group["amount"], label=name, color=colors.get(name), alpha=0.8)
ax.set_title("按分类看数量与销售额")
ax.set_xlabel("数量")
ax.set_ylabel("销售额")
ax.legend()
plt.tight_layout()
