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

total = monthly.groupby("month", as_index=False)["revenue"].sum()
by_region = monthly.groupby("region")["revenue"].sum().sort_values(ascending=False)

fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
axes[0, 0].plot(total["month"], total["revenue"], marker="o", color="#4C78A8")
axes[0, 0].set_title("折线：12 个月怎么变")
axes[0, 0].set_ylabel("销售额（元）")

axes[0, 1].bar(by_region.index, by_region.values, color="#4C78A8")
axes[0, 1].set_title("柱状：地区之间谁更大")
axes[0, 1].set_ylabel("销售额（元）")

axes[1, 0].scatter(monthly["orders"], monthly["revenue"], s=18, alpha=0.65, color="#4C78A8")
axes[1, 0].set_title("散点：订单数和销售额的关系")
axes[1, 0].set_xlabel("订单数")
axes[1, 0].set_ylabel("销售额（元）")

axes[1, 1].hist(total["revenue"], bins=6, color="#4C78A8", edgecolor="white")
axes[1, 1].set_title("直方图：月度销售额的分布")
axes[1, 1].set_xlabel("销售额（元）")
axes[1, 1].set_ylabel("月份数")

for ax in axes.flat:
    ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("同一份销售数据，四种问法", fontsize=15)
fig.tight_layout()
fig.savefig(out / "chart-choice.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "chart-choice.png")))
plt.close(fig)
print("折线看趋势，柱状比大小，散点看关系，直方图看分布")


sales = pd.read_csv(data_path("sales.csv"))
sales["amount"] = sales["units"] * sales["price"]

fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(sales["units"], sales["amount"], s=55, color="#4C78A8", alpha=0.8)
ax.set_xlabel("购买数量")
ax.set_ylabel("订单金额（元）")
ax.set_title("订单明细：数量与金额")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "sales-scatter.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "sales-scatter.png")))
plt.close(fig)

print("订单数:", len(sales))
print("数量与金额的相关系数:", round(sales["units"].corr(sales["amount"]), 3))


choices = [
    ("12 个月销售额怎么变", "折线图", "时间连续，关注趋势和拐点"),
    ("哪个地区销售额最高", "柱状图", "类别之间比大小，排序后更清楚"),
    ("订单数和金额是否相关", "散点图", "每条记录一个点，看两个数值的关系"),
    ("月度销售额集中在哪里", "直方图", "把连续数值分段，看分布形状"),
]
for question, chart, reason in choices:
    print(f"{question} -> {chart}：{reason}")
