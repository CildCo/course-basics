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
import seaborn as sns

sns.set_theme(
    style="whitegrid",
    rc={
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.6))
sns.boxplot(data=monthly, x="region", y="revenue", width=0.5, color="#B8CCE4", ax=ax)
sns.stripplot(data=monthly, x="region", y="revenue", color="#2F3E4E", size=3, alpha=0.55, ax=ax)
ax.set_xlabel("地区")
ax.set_ylabel("月度销售额（元）")
ax.set_title("地区之间的分布差异")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "box-region.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "box-region.png")))
plt.close(fig)
print("每个箱体由 36 条月度记录计算得到")


rows = []
for (region_name, category), group in monthly.groupby(["region", "category"]):
    q1 = group["revenue"].quantile(0.25)
    q3 = group["revenue"].quantile(0.75)
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    for _, row in group[group["revenue"] > upper].iterrows():
        rows.append(
            {
                "月份": row["month"].strftime("%Y-%m"),
                "地区": region_name,
                "分类": category,
                "销售额": round(row["revenue"], 0),
                "上界": round(upper, 0),
            }
        )

outliers = pd.DataFrame(rows)
print("按 1.5 倍 IQR 规则找到的异常值:")
print(outliers.to_string(index=False) if len(outliers) else "没有")


fig, ax = plt.subplots(figsize=(8, 4.6))
sns.violinplot(
    data=monthly,
    x="category",
    y="revenue",
    hue="category",
    inner="quartile",
    palette=["#A7C4E4", "#F2C57C", "#9CC5A1"],
    legend=False,
    ax=ax,
)
ax.set_xlabel("分类")
ax.set_ylabel("月度销售额（元）")
ax.set_title("分类内部的分布形状")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "violin-category.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "violin-category.png")))
plt.close(fig)

stats = monthly.groupby("category")["revenue"].agg(["median", "std"]).round(0)
print(stats.to_string())


numeric = monthly[["orders", "revenue", "avg_order_value", "return_rate", "revenue_last_year"]]
corr = numeric.corr()

fig, ax = plt.subplots(figsize=(6.5, 5))
sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    center=0,
    square=True,
    linewidths=0.6,
    cbar_kws={"shrink": 0.8},
    ax=ax,
)
ax.set_title("数值列相关性")
fig.tight_layout()
fig.savefig(out / "corr-heatmap.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "corr-heatmap.png")))
plt.close(fig)
print("全表订单数与销售额相关系数:", round(corr.loc["orders", "revenue"], 3))
print("按分类拆开后:")
for category, group in monthly.groupby("category"):
    print(f"  {category}: {group['orders'].corr(group['revenue']):.3f}")
print("平均客单价与销售额相关系数:", round(corr.loc["avg_order_value", "revenue"], 3))


fig, ax = plt.subplots(figsize=(7.5, 4.6))
sns.scatterplot(
    data=monthly,
    x="orders",
    y="revenue",
    hue="category",
    palette={"办公": "#4C78A8", "数码": "#E45756", "家居": "#54A24B"},
    s=48,
    alpha=0.8,
    ax=ax,
)
spike = monthly[
    (monthly["month"].dt.strftime("%Y-%m") == "2026-12")
    & (monthly["region"] == "华中")
    & (monthly["category"] == "数码")
].iloc[0]
ax.annotate(
    "12 月华中数码大促",
    xy=(spike["orders"], spike["revenue"]),
    xytext=(-110, 20),
    textcoords="offset points",
    arrowprops={"arrowstyle": "->", "color": "#555555"},
    fontsize=9,
)
ax.set_xlabel("订单数")
ax.set_ylabel("销售额（元）")
ax.set_title("订单数与销售额：分类之间的斜率不同")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "scatter-orders.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "scatter-orders.png")))
plt.close(fig)
print("异常点销售额:", f"{spike['revenue']:,.0f}", "元")
