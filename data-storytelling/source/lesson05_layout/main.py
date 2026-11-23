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

total = sales["revenue"].sum()
peak = monthly.loc[monthly["revenue"].idxmax()]
last = monthly.iloc[-1]
east_share = region_revenue["华东"] / total
digital_share = category_revenue["数码"] / total

print(f"总销售额：{total / 10000:.1f} 万元")
print(f"峰值月：{peak['month'].month} 月，{peak['revenue'] / 10000:.1f} 万元")
print(f"华东占比：{east_share:.1%}")
print(f"数码占比：{digital_share:.1%}")


fig = plt.figure(figsize=(12.5, 9.0))
gs = fig.add_gridspec(4, 3, height_ratios=[0.55, 0.55, 1.7, 1.0],
                      hspace=0.55, wspace=0.32)

header = fig.add_subplot(gs[0, :])
header.axis("off")
header.text(0, 0.95, "2026 年上半年销售分析", fontsize=23, fontweight="bold",
            color=INK, va="top")
header.text(0, 0.35,
            f"销售额 {total / 10000:.1f} 万元，4 月见顶后回落，数码与西南仍在增长",
            fontsize=11.5, color="#666666", va="top")

kpis = [
    ("总销售额", f"{total / 10000:.1f} 万元"),
    ("峰值月份", f"{peak['month'].month} 月"),
    ("华东占比", f"{east_share:.1%}"),
]
for i, (label, value) in enumerate(kpis):
    ax = fig.add_subplot(gs[1, i])
    ax.axis("off")
    ax.text(0, 0.85, label, fontsize=10, color="#777777", va="top")
    ax.text(0, 0.42, value, fontsize=18, fontweight="bold", color=PRIMARY, va="top")

ax_trend = fig.add_subplot(gs[2, :2])
ax_trend.plot(monthly["month"], monthly["revenue"] / 10000,
              color=PRIMARY, linewidth=2.4, marker="o", markersize=5)
ax_trend.scatter([peak["month"]], [peak["revenue"] / 10000], s=90, color=ACCENT, zorder=3)
ax_trend.annotate("4 月见顶", xy=(peak["month"], peak["revenue"] / 10000),
                  xytext=(peak["month"], peak["revenue"] / 10000 + 1.5),
                  ha="center", fontsize=10, color=ACCENT)
ax_trend.set_title("月度销售额（万元）", loc="left", fontsize=12)
ax_trend.spines[["top", "right"]].set_visible(False)
ax_trend.grid(axis="y", color="#EEEEEE")
ax_trend.set_axisbelow(True)

ax_region = fig.add_subplot(gs[2, 2])
ordered = region_revenue.sort_values()
colors = [MUTED] * len(ordered)
colors[-1] = PRIMARY
ax_region.barh(ordered.index, ordered.values / 10000, color=colors, height=0.6)
ax_region.set_title("地区销售额（万元）", loc="left", fontsize=12)
ax_region.set_xlabel("万元")
ax_region.spines[["top", "right"]].set_visible(False)
ax_region.grid(axis="x", color="#EEEEEE")
ax_region.set_axisbelow(True)

ax_note = fig.add_subplot(gs[3, :2])
ax_note.axis("off")
ax_note.text(0, 1.0, "结论", fontsize=12, fontweight="bold", color=ACCENT, va="top")
ax_note.text(0, 0.72,
             "整体在 4 月见顶，5-6 月走弱主要来自华东；\n"
             "数码和西南保持增长，是下半年的抓手。",
             fontsize=11, color=INK, va="top", linespacing=1.7)
ax_note.text(0, 0.18, "行动：复盘华东下滑 / 复制华南西南动作 / 数码优先备货",
             fontsize=9.5, color="#666666", va="top")

ax_category = fig.add_subplot(gs[3, 2])
ax_category.bar(category_revenue.index, category_revenue.values / total * 100,
                color=[PRIMARY, MUTED], width=0.55)
for i, value in enumerate(category_revenue.values / total * 100):
    ax_category.text(i, value + 1.5, f"{value:.1f}%", ha="center", fontsize=9.5, color=INK)
ax_category.set_ylim(0, 72)
ax_category.set_title("品类占比", loc="left", fontsize=12)
ax_category.set_ylabel("%")
ax_category.spines[["top", "right"]].set_visible(False)
ax_category.grid(axis="y", color="#EEEEEE")
ax_category.set_axisbelow(True)

fig.text(0.01, 0.01, "数据来源：assets/sales.csv（2026 年 1-6 月）；销售额未扣退款",
         fontsize=9, color="#888888")
fig.savefig(out / "lesson05-layout.png", dpi=140, bbox_inches="tight")
display(Image(filename=str(out / "lesson05-layout.png")))
plt.close(fig)
print("一页排版已保存：", (out / "lesson05-layout.png").name)


outline = """# 2026 年上半年销售分析报告

## 摘要
- 总销售额：168.5 万元
- 峰值月份：4 月
- 第一大地区：华东

## 结论
整体在 4 月见顶，5-6 月走弱主要来自华东；数码与西南保持增长。

## 证据
1. 月度趋势：4 月见顶，6 月较 4 月回落。
2. 地区结构：华东占比最高，但 5-6 月回落。
3. 品类结构：数码占比接近六成，6 月较 1 月增长。

## 行动
1. 复盘华东 5-6 月下滑原因。
2. 复制华南、西南的增长动作。
3. 数码优先备货，家居做结构优化。

## 附录
- 数据范围：2026 年 1-6 月，四个地区，两个品类。
- 口径：销售额为订单金额合计，未扣退款。
- 明细：见 assets/sales.csv。
"""
(out / "lesson05-outline.md").write_text(outline, encoding="utf-8")
print(outline)
print("已写入：", (out / "lesson05-outline.md").name)
