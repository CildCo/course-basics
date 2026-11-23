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
category = df.groupby("category")["amount"].sum().sort_values()


fig, ax = plt.subplots(figsize=(6, 3.5))
colors = ["#c7d2e3", "#93b4ff", "#4f7cff"]
bars = ax.bar(category.index, category.values, color=colors)
ax.set_title("分类销售额", fontsize=13)
ax.set_ylabel("销售额")
for bar, value in zip(bars, category.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()


fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(category.index, category.values, marker="o", color="#4f7cff")
ax.set_title("分类销售额走势")
ax.annotate("最高", xy=(category.index[-1], category.values[-1]), xytext=(0, 8), textcoords="offset points", ha="center", color="#d97706")
plt.tight_layout()
