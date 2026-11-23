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

peak = monthly.loc[monthly["revenue"].idxmax()]
last = monthly.iloc[-1]
peak_to_last = last["revenue"] / peak["revenue"] - 1
months = monthly["month"].dt.strftime("%m月")
values = monthly["revenue"] / 10000

print("峰值：", peak["month"].strftime("%m月"), f"{peak['revenue'] / 10000:.1f} 万元")
print("6 月较峰值：", f"{peak_to_last:.1%}")


fig, ax = plt.subplots(figsize=(9.5, 5.2))

ax.plot(monthly["month"], values, color=MUTED, linewidth=2.2, zorder=2)
ax.plot(monthly["month"].iloc[3:], values.iloc[3:],
        color=ACCENT, linewidth=2.8, marker="o", markersize=6, zorder=3)
ax.scatter(monthly["month"].iloc[3], values.iloc[3], s=70, color=ACCENT, zorder=4)

ax.annotate(
    f"6 月较 4 月高点回落 {abs(peak_to_last):.1%}",
    xy=(monthly["month"].iloc[-1], values.iloc[-1]),
    xytext=(monthly["month"].iloc[1], values.iloc[-1] - 1.8),
    fontsize=10, color=ACCENT,
    arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2),
)
ax.set_ylim(values.min() - 3, values.max() + 2)
ax.set_ylabel("销售额（万元）")
ax.set_title("上半年销售额在 4 月见顶", loc="left", fontsize=15, fontweight="bold", pad=14)
ax.text(0, 1.02, "5-6 月连续回落，6 月比 4 月少 3.9%",
        transform=ax.transAxes, fontsize=10, color="#666666")

ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
ax.set_axisbelow(True)
fig.text(0.01, -0.02, "数据来源：assets/sales.csv（2026 年 1-6 月）",
         fontsize=9, color="#888888")
fig.tight_layout()
fig.savefig(out / "lesson03-annotation.png", dpi=140, bbox_inches="tight")
display(Image(filename=str(out / "lesson03-annotation.png")))
plt.close(fig)


fig, ax = plt.subplots(figsize=(8.6, 4.6))
ordered = region_revenue.sort_values()
colors = [MUTED] * len(ordered)
colors[-1] = PRIMARY
bars = ax.barh(ordered.index, ordered.values / 10000, color=colors, height=0.6)

total = sales["revenue"].sum()
for bar, value in zip(bars, ordered.values):
    ax.text(value / 10000 + 1.5, bar.get_y() + bar.get_height() / 2,
            f"{value / 10000:.1f} 万（{value / total:.1%}）",
            va="center", fontsize=9.5, color=INK)

ax.set_xlim(0, ordered.max() / 10000 * 1.28)
ax.set_xlabel("销售额（万元）")
ax.set_title("华东贡献近四成销售额", loc="left", fontsize=15, fontweight="bold", pad=14)
ax.text(0, 1.02, f"第一名占比 {region_revenue.iloc[0] / total:.1%}，其余地区合计仍超过六成",
        transform=ax.transAxes, fontsize=10, color="#666666")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color="#EEEEEE", linewidth=0.8)
ax.set_axisbelow(True)
fig.text(0.01, -0.04, "数据来源：assets/sales.csv（2026 年 1-6 月）",
         fontsize=9, color="#888888")
fig.tight_layout()
fig.savefig(out / "lesson03-hierarchy.png", dpi=140, bbox_inches="tight")
display(Image(filename=str(out / "lesson03-hierarchy.png")))
plt.close(fig)
print("两张图已保存：lesson03-annotation.png、lesson03-hierarchy.png")
