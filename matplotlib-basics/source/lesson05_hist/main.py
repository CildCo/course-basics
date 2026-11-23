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
df["amount"].describe()


fig, ax = plt.subplots(figsize=(6, 3.5))
ax.hist(df["amount"], bins=8, color="#4f7cff", edgecolor="white")
ax.set_title("销售额分布")
ax.set_xlabel("销售额")
ax.set_ylabel("记录数")
plt.tight_layout()


fig, ax = plt.subplots(figsize=(6, 3.5))
ax.hist(df["amount"], bins=15, color="#2f8f5b", edgecolor="white")
ax.axvline(df["amount"].mean(), color="#d97706", linestyle="--", label="均值")
ax.axvline(df["amount"].median(), color="#7c5cfc", linestyle=":", label="中位数")
ax.set_title("销售额分布与中心位置")
ax.legend()
plt.tight_layout()
