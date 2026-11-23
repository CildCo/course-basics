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
detail["segment"] = detail["segment"].fillna("未知")
detail["revenue"] = detail["quantity"] * detail["unit_price"]

print("明细:", detail.shape)
print("城市数:", detail["city"].nunique(), "客群数:", detail["segment"].nunique())


summary = (detail.groupby(["city", "segment"])
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
        avg_quantity=("quantity", "mean"),
        max_order=("revenue", "max"),
    )
    .round(2)
    .sort_values("revenue", ascending=False))
print("分组数:", len(summary))
print(summary.head(10).to_string())


detail["city_revenue"] = detail.groupby("city")["revenue"].transform("sum")
detail["city_share"] = (detail["revenue"] / detail["city_revenue"]).round(3)
detail["city_rank"] = detail.groupby("city")["revenue"].rank(ascending=False, method="dense").astype(int)

print("明细行数:", len(detail), "分组结果行数:", len(summary))
print(detail[["order_id", "city", "revenue", "city_revenue", "city_share", "city_rank"]].head(8).to_string(index=False))


def top_product(frame):
    grouped = frame.groupby("product_name")["revenue"].sum()
    return pd.Series({"top_product": grouped.idxmax(), "top_revenue": grouped.max()})


top_by_city = detail.groupby("city")[["product_name", "revenue"]].apply(top_product)
print("apply 结果行数:", len(top_by_city))
print(top_by_city.sort_values("top_revenue", ascending=False).to_string())


timeline = detail.sort_values(["city", "order_date"]).copy()
timeline["city_cum_revenue"] = timeline.groupby("city")["revenue"].cumsum()
last = timeline.groupby("city").tail(1)
print(last[["city", "order_date", "city_cum_revenue"]].to_string(index=False))


by_channel_category = (detail.groupby(["channel", "category"], as_index=False)
    .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")))
by_channel_category["avg_order"] = (by_channel_category["revenue"] / by_channel_category["orders"]).round(2)
print(by_channel_category.sort_values(["channel", "revenue"], ascending=[True, False]).to_string(index=False))
