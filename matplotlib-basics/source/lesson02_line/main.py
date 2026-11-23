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
monthly = df.assign(month=df["date"].dt.to_period("M")).groupby("month")["amount"].sum()
monthly


fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(monthly.index.astype(str), monthly.values, marker="o", linewidth=2)
ax.set_title("月度销售额")
ax.set_xlabel("月份")
ax.set_ylabel("销售额")
plt.xticks(rotation=30)
plt.tight_layout()
