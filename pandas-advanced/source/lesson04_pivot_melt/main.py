from pathlib import Path

from IPython.display import Image, display

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

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

orders = pd.read_csv(data_path("orders.csv"), parse_dates=["order_date"])
customers = pd.read_csv(data_path("customers.csv"))
products = pd.read_csv(data_path("products.csv"))

detail = (orders
    .merge(customers, on="customer_id", how="left")
    .merge(products, on="product_id", how="left"))
detail["city"] = detail["city"].fillna("未知")
detail["segment"] = detail["segment"].fillna("未知")
detail["revenue"] = detail["quantity"] * detail["unit_price"]

print("明细:", detail.shape)
print("城市:", sorted(detail["city"].unique()))
print("品类:", sorted(detail["category"].unique()))


pivot = detail.pivot_table(
    index="city",
    columns="category",
    values="revenue",
    aggfunc="sum",
    fill_value=0,
    margins=True,
    margins_name="合计",
).round(0)
print(pivot.to_string())


import seaborn as sns

plot_data = pivot.drop(index="合计").drop(columns="合计")
fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(plot_data, annot=True, fmt=".0f", cmap="Blues", linewidths=0.6, ax=ax)
ax.set_title("城市 × 品类销售额")
ax.set_xlabel("品类")
ax.set_ylabel("城市")
fig.tight_layout()
fig.savefig(out / "pivot-heatmap.png", dpi=120)
display(Image(filename=str(out / "pivot-heatmap.png")))
plt.close(fig)
print("参与绘图的形状:", plot_data.shape)


multi = detail.pivot_table(
    index="channel",
    columns="category",
    values="revenue",
    aggfunc=["sum", "count"],
    fill_value=0,
).round(0)
print(multi.to_string())
print("列层级:", multi.columns.names)

city_channel = detail.pivot_table(
    index="city",
    columns="channel",
    values="order_id",
    aggfunc="nunique",
    fill_value=0,
)
print("\n城市 × 渠道订单数：")
print(city_channel.to_string())


long = (plot_data.reset_index()
    .melt(id_vars="city", var_name="category", value_name="revenue"))
print("宽表:", plot_data.shape, "长表:", long.shape)
print(long.sort_values("revenue", ascending=False).head(8).to_string(index=False))


counts = pd.crosstab(detail["segment"], detail["category"], margins=True, margins_name="合计")
print("订单数交叉表：")
print(counts.to_string())

share = pd.crosstab(detail["segment"], detail["category"], normalize="index").round(2)
print("\n按客群归一化的占比：")
print(share.to_string())
