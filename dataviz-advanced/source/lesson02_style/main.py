from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

monthly = pd.read_csv(data_path("monthly.csv"))
monthly["month"] = pd.to_datetime(monthly["month"])
print("月度汇总:", monthly.shape[0], "行")
print(monthly.head(3).to_string(index=False))


from IPython.display import Image, display
import matplotlib.pyplot as plt

region = monthly.groupby("region")["revenue"].sum().sort_values(ascending=False) / 10000

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].bar(region.index, region.values)
axes[0].set_title("默认样式")
axes[1].bar(region.index, region.values, color="#4C78A8")
axes[1].set_title("统一颜色")

for ax in axes:
    ax.set_ylabel("销售额（万元）")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "style-compare.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "style-compare.png")))
plt.close(fig)
print("统一颜色只是第一步，接下来要建立主次")


fig, ax = plt.subplots(figsize=(8.5, 4.6))
bars = ax.barh(region.index[::-1], region.values[::-1], color="#A7C4E4", height=0.62)
for bar, value in zip(bars, region.values[::-1]):
    ax.text(value + 2, bar.get_y() + bar.get_height() / 2, f"{value:.1f}", va="center", fontsize=10)

ax.set_xlim(0, region.max() * 1.18)
ax.set_xlabel("销售额（万元）")
ax.set_title("华东仍是第一大市场", loc="left", fontsize=16, fontweight="bold", pad=30)
ax.text(
    0, 1.02,
    "2026 年各地区销售额，单位：万元",
    transform=ax.transAxes, fontsize=10, color="#666666",
)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color="#DDDDDD", linewidth=0.8)
ax.set_axisbelow(True)
fig.text(0.01, -0.04, "数据来源：课程示例 monthly.csv", fontsize=8, color="#888888")
fig.tight_layout()
fig.savefig(out / "styled-bars.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "styled-bars.png")))
plt.close(fig)
print("标题:", ax.get_title(loc="left"))
print("直接标注省去读者对照坐标轴")


colors = ["#D64545" if name == region.idxmax() else "#C9D6E8" for name in region.index]
fig, ax = plt.subplots(figsize=(8, 4.2))
bars = ax.bar(region.index, region.values, color=colors, width=0.58)
top_name = region.idxmax()
top_value = region.loc[top_name]
for bar, value in zip(bars, region.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2, value + 2, f"{value:.1f}",
        ha="center", fontsize=10,
    )
ax.annotate(
    f"重点：{top_name}贡献 {top_value / region.sum():.1%}",
    xy=(list(region.index).index(top_name), top_value),
    xytext=(0, 34), textcoords="offset points",
    ha="center", fontsize=10, color="#D64545",
    arrowprops={"arrowstyle": "->", "color": "#D64545"},
)
ax.set_ylim(0, region.max() * 1.22)
ax.set_ylabel("销售额（万元）")
ax.set_title("重点只有一个：华东", loc="left", fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "accent.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "accent.png")))
plt.close(fig)
print(f"{top_name}占比: {top_value / region.sum():.1%}")
