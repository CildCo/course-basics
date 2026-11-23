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

pivot = monthly.pivot_table(index="month", columns=["region", "category"], values="revenue", aggfunc="sum")
fig, ax = plt.subplots(figsize=(10, 4.8))
for column in pivot.columns:
    ax.plot(pivot.index, pivot[column], linewidth=1.2, alpha=0.85)
ax.set_title("12 条线挤在一张图里")
ax.set_ylabel("销售额（元）")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "spaghetti.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "spaghetti.png")))
plt.close(fig)
print("图里有", pivot.shape[1], "条线，读者很难把线和地区、分类对上")


import seaborn as sns

sns.set_theme(
    style="whitegrid",
    rc={
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
    },
)

g = sns.relplot(
    data=monthly,
    x="month",
    y="revenue",
    hue="category",
    col="region",
    col_wrap=2,
    kind="line",
    height=2.9,
    aspect=1.5,
    facet_kws={"sharey": True},
)
g.set_axis_labels("月份", "销售额（元）")
g.set_titles("{col_name}")
g.figure.suptitle("分地区看 12 个月走势", y=1.02)
g.figure.autofmt_xdate()
g.savefig(out / "small-multiples.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "small-multiples.png")))
plt.close(g.figure)
print("4 个地区 × 3 个分类 = 12 条线，被拆成 4 个可比的小图")


colors = {"办公": "#4C78A8", "数码": "#E45756", "家居": "#54A24B"}
fig, axes = plt.subplots(2, 2, figsize=(11, 6), sharex=True, sharey=True)
for ax, (region_name, frame) in zip(axes.flat, monthly.groupby("region")):
    for category, part in frame.groupby("category"):
        ax.plot(part["month"], part["revenue"], label=category, color=colors[category], linewidth=1.6)
    ax.set_title(region_name, loc="left")
    ax.spines[["top", "right"]].set_visible(False)

axes[0, 0].legend(title="分类", frameon=False, loc="upper left")
fig.suptitle("同样的分面，用 subplots 控制布局", fontsize=14)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(out / "subplot-grid.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "subplot-grid.png")))
plt.close(fig)
print("共享 x、y 轴，格子之间可以直接比高度")


summary = monthly.groupby(["region", "category"], as_index=False)["revenue"].sum()
top_index = summary.groupby("region")["revenue"].idxmax()
top = summary.loc[top_index].sort_values("revenue", ascending=False)
top["revenue"] = (top["revenue"] / 10000).round(1)
top = top.rename(columns={"revenue": "销售额（万元）"})
print(top.to_string(index=False))
