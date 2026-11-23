from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, display


np.random.seed(42)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = data_path("sales.csv").parent.parent / "output"
out.mkdir(exist_ok=True)

sales = pd.read_csv(data_path("sales.csv"))
sales["month"] = pd.to_datetime(sales["month"], format="%Y-%m")

PRIMARY = "#2F5D8A"
ACCENT = "#D64545"
MUTED = "#B8CCE4"
INK = "#333333"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": INK,
    "xtick.color": "#666666",
    "ytick.color": "#666666",
})

print("数据行数:", len(sales))
print(sales.head(4).to_string(index=False))

monthly = sales.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
region_revenue = sales.groupby("region")["revenue"].sum().sort_values(ascending=False)
category_revenue = sales.groupby("category")["revenue"].sum().sort_values(ascending=False)

print("月度销售额（万元）：")
print((monthly.set_index("month")["revenue"] / 10000).round(1).to_string())
print("\n地区销售额（万元）：")
print((region_revenue / 10000).round(1).to_string())
print("\n订单数范围：", int(sales["orders"].min()), "到", int(sales["orders"].max()))


fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.8))
ax1, ax2, ax3, ax4 = axes.flat

ax1.plot(monthly["month"], monthly["revenue"] / 10000,
         color=PRIMARY, linewidth=2.2, marker="o", markersize=5)
ax1.set_title("趋势：销售额随月份怎么变？", loc="left")
ax1.set_ylabel("销售额（万元）")

ax2.bar(region_revenue.index, region_revenue.values / 10000, color=PRIMARY, width=0.62)
ax2.set_title("对比：哪个地区卖得最多？", loc="left")
ax2.set_ylabel("销售额（万元）")

ax3.hist(sales["orders"], bins=8, color=PRIMARY, edgecolor="white")
ax3.set_title("分布：单月单品类订单数集中在哪？", loc="left")
ax3.set_xlabel("订单数")
ax3.set_ylabel("记录数")

ax4.scatter(sales["orders"], sales["revenue"] / 10000,
            s=42, color=PRIMARY, alpha=0.7, edgecolor="white", linewidth=0.5)
ax4.set_title("关系：订单越多，销售额越高吗？", loc="left")
ax4.set_xlabel("订单数")
ax4.set_ylabel("销售额（万元）")

for ax in axes.flat:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#EEEEEE", linewidth=0.8)
    ax.set_axisbelow(True)

fig.suptitle("同一份销售数据，四个问题，四种图", x=0.02, ha="left",
             fontsize=17, fontweight="bold")
fig.tight_layout()
fig.savefig(out / "lesson02-chart-choice.png", dpi=130, bbox_inches="tight")
display(Image(filename=str(out / "lesson02-chart-choice.png")))
plt.close(fig)
print("相关系数（订单数 vs 销售额）：", round(sales["orders"].corr(sales["revenue"]), 3))


questions = pd.DataFrame([
    ("销售额随时间怎么变", "折线图", "时间是连续顺序，关注趋势和拐点"),
    ("哪个地区销售额最高", "柱状图", "比较分类之间的大小，排序后更清楚"),
    ("订单数如何分布", "直方图", "看集中区间、偏斜和长尾"),
    ("订单数与销售额是否同向", "散点图", "每条记录一个点，观察两个数值的关系"),
    ("各品类占比是多少", "横向条形图", "占比用长度比较，比饼图更易读"),
], columns=["问题", "图表", "理由"])
print(questions.to_string(index=False))
questions.to_csv(out / "lesson02-chart-choice.csv", index=False, encoding="utf-8-sig")
print("\n已写入：", (out / "lesson02-chart-choice.csv").name)
