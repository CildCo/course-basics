from pathlib import Path

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
detail["revenue"] = detail["quantity"] * detail["unit_price"]

print("明细:", detail.shape)
print(detail.head(3)[["order_id", "channel", "category", "city", "revenue"]].to_string(index=False))


indexed = detail.set_index(["channel", "category"]).sort_index()
print("索引层级:", indexed.index.names)
print("渠道:", list(indexed.index.levels[0]))
print("品类:", list(indexed.index.levels[1]))
print(indexed[["order_id", "revenue"]].head(6).to_string())


online = indexed.loc["线上"]
print("线上渠道订单数:", len(online))
print("线上-音频 小计:", round(float(indexed.loc[("线上", "音频"), "revenue"].sum()), 2))

audio = indexed.xs("音频", level="category").reset_index()
print("\n音频在各渠道的明细：")
print(audio[["channel", "order_id", "revenue"]].to_string(index=False))


channel_category = detail.groupby(["channel", "category"])["revenue"].sum()
print(channel_category.sort_values(ascending=False).to_string())

channel_total = indexed.groupby(level="channel")["revenue"].agg(["sum", "count", "mean"]).round(2)
print("\n按渠道汇总：")
print(channel_total.to_string())


swapped = channel_category.swaplevel().sort_index()
print("交换层级后前 8 行：")
print(swapped.head(8).to_string())

wide = channel_category.unstack("category", fill_value=0)
print("\n展开成宽表：")
print(wide.round(0).to_string())
print("宽表形状:", wide.shape)


city_total = detail.groupby("city")["revenue"].sum().rename("city_revenue")
with_city = detail.set_index("city").join(city_total)
print(with_city[["order_id", "city_revenue"]].head(5).to_string())
print("明细行数:", len(with_city), "城市数:", city_total.size)


export = channel_category.rename("revenue").reset_index()
print(export.head(8).to_string(index=False))
print("列名:", export.columns.tolist())
