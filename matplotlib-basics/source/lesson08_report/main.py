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
category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
monthly = df.assign(month=df["date"].dt.to_period("M")).groupby("month")["amount"].sum()
print("总销售额：", round(df["amount"].sum(), 2))
print("最高分类：", category.index[0], round(category.iloc[0], 2))
print("最高月份：", str(monthly.idxmax()), round(monthly.max(), 2))


fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].bar(category.index, category.values, color=["#4f7cff", "#2f8f5b", "#d97706"])
axes[0].set_title("分类销售额")
axes[0].set_ylabel("销售额")
axes[1].plot(monthly.index.astype(str), monthly.values, marker="o", color="#7c5cfc")
axes[1].set_title("月度销售额")
axes[1].tick_params(axis="x", rotation=30)
fig.suptitle("销售分析：数码最高，5 月是峰值")
plt.tight_layout()


from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
fig.savefig(output / "sales_report.png", dpi=150)
print("报告图片：", (output / "sales_report.png").exists())
print("建议：优先补货数码，复盘 5 月活动。")
