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
region_month = sales.pivot_table(index="month", columns="region", values="revenue", aggfunc="sum")

east = sales[sales["region"] == "华东"]
east_mar_apr = east[east["month"].isin(pd.to_datetime(["2026-03", "2026-04"]))]["revenue"].sum()
east_may_jun = east[east["month"].isin(pd.to_datetime(["2026-05", "2026-06"]))]["revenue"].sum()
east_change = east_may_jun / east_mar_apr - 1

digital = sales[sales["category"] == "数码"]
digital_jan = digital[digital["month"] == pd.Timestamp("2026-01-01")]["revenue"].sum()
digital_jun = digital[digital["month"] == pd.Timestamp("2026-06-01")]["revenue"].sum()
digital_growth = digital_jun / digital_jan - 1

southwest = sales[sales["region"] == "西南"]
sw_jan = southwest[southwest["month"] == pd.Timestamp("2026-01-01")]["revenue"].sum()
sw_jun = southwest[southwest["month"] == pd.Timestamp("2026-06-01")]["revenue"].sum()
sw_growth = sw_jun / sw_jan - 1

peak = monthly.loc[monthly["revenue"].idxmax()]
last = monthly.iloc[-1]
print(f"4 月峰值：{peak['revenue'] / 10000:.1f} 万元")
print(f"6 月：{last['revenue'] / 10000:.1f} 万元，较 4 月 {last['revenue'] / peak['revenue'] - 1:.1%}")
print(f"华东 5-6 月较 3-4 月：{east_change:.1%}")
print(f"数码 6 月较 1 月：{digital_growth:.1%}")
print(f"西南 6 月较 1 月：{sw_growth:.1%}")
print(f"数码销售额占比：{digital['revenue'].sum() / sales['revenue'].sum():.1%}")


fig, ax = plt.subplots(figsize=(9.8, 5.2))
for region in region_month.columns:
    color = ACCENT if region == "华东" else MUTED
    width = 2.8 if region == "华东" else 1.8
    ax.plot(region_month.index, region_month[region] / 10000,
            color=color, linewidth=width, marker="o", markersize=4, label=region)

ax.annotate(
    f"华东 5-6 月合计\n较 3-4 月 {east_change:.1%}",
    xy=(pd.Timestamp("2026-06-01"), region_month.loc[pd.Timestamp("2026-06-01"), "华东"] / 10000),
    xytext=(pd.Timestamp("2026-01-15"), 3.2),
    fontsize=10, color=ACCENT,
    arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2),
)
ax.set_ylabel("销售额（万元）")
ax.set_title("整体走弱主要来自华东", loc="left", fontsize=15, fontweight="bold", pad=14)
ax.text(0, 1.02, "其他三个地区保持平稳或增长，华东 5-6 月明显回落",
        transform=ax.transAxes, fontsize=10, color="#666666")
ax.legend(frameon=False, ncol=4, loc="upper right", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
ax.set_axisbelow(True)
fig.text(0.01, -0.03, "数据来源：assets/sales.csv；销售额为订单金额合计，未扣退款",
         fontsize=9, color="#888888")
fig.tight_layout()
fig.savefig(out / "lesson04-evidence.png", dpi=140, bbox_inches="tight")
display(Image(filename=str(out / "lesson04-evidence.png")))
plt.close(fig)


claim = "上半年销售额在 4 月见顶，5-6 月走弱主要来自华东。"
evidence = [
    f"4 月销售额 {peak['revenue'] / 10000:.1f} 万元，为半年最高。",
    f"6 月销售额 {last['revenue'] / 10000:.1f} 万元，较 4 月下降 {abs(last['revenue'] / peak['revenue'] - 1):.1%}。",
    f"华东 5-6 月合计销售额较 3-4 月下降 {abs(east_change):.1%}，同期其他地区未出现同等幅度回落。",
    f"数码品类 6 月较 1 月增长 {digital_growth:.1%}，西南地区 6 月较 1 月增长 {sw_growth:.1%}。",
]
scope = "2026 年 1-6 月，华东、华南、华北、西南四个地区，数码与家居两个品类；销售额为订单金额合计，未扣退款。"
boundary = "数据只有半年，没有上年同期，无法计算同比；也没有促销、库存和渠道数据，不能判断华东下滑的具体原因。相关变化不等于因果关系。"

report = "\n".join([
    "【结论】", claim, "",
    "【证据】", *[f"- {item}" for item in evidence], "",
    "【范围】", scope, "",
    "【边界】", boundary,
])
(out / "lesson04-conclusion.txt").write_text(report + "\n", encoding="utf-8")
print(report)
print("\n已写入：", (out / "lesson04-conclusion.txt").name)
