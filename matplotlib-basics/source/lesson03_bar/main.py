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
category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
category


fig, ax = plt.subplots(figsize=(6, 3.5))
bars = ax.bar(category.index, category.values, color="#4f7cff")
ax.set_title("分类销售额")
ax.set_ylabel("销售额")
for bar, value in zip(bars, category.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.0f}", ha="center", va="bottom")
plt.tight_layout()


fig, ax = plt.subplots(figsize=(6, 3.5))
ax.barh(category.index, category.values, color="#2f8f5b")
ax.set_title("分类销售额（横向）")
ax.set_xlabel("销售额")
plt.tight_layout()
