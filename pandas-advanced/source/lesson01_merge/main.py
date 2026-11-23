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

print("订单表:", orders.shape)
print("客户表:", customers.shape)
print("商品表:", products.shape)
print(orders.head(3).to_string(index=False))


left_join = orders.merge(customers, on="customer_id", how="left", indicator=True)
print("订单行数:", len(orders), "合并后:", len(left_join))
print(left_join["_merge"].value_counts().to_string())
print(left_join.loc[left_join["_merge"] == "left_only", ["order_id", "customer_id", "product_id"]].to_string(index=False))


left_keys = pd.DataFrame({"customer_id": ["C01", "C02", "C03"], "source": ["A", "B", "C"]})
right_keys = pd.DataFrame({"customer_id": ["C02", "C03", "C04"], "coupon": [10, 20, 30]})

for how in ["inner", "left", "right", "outer"]:
    result = left_keys.merge(right_keys, on="customer_id", how=how)
    print(f"{how:5s} 行数={len(result)} 键={result['customer_id'].tolist()}")

print(left_keys.merge(right_keys, on="customer_id", how="outer").to_string(index=False))


promotions = pd.DataFrame({
    "product_id": ["P01", "P01", "P04"],
    "campaign": ["新年特惠", "会员日", "清仓"],
})

promoted = orders.merge(promotions, on="product_id", how="left")
print("合并前:", len(orders), "合并后:", len(promoted))
print(promoted.loc[promoted["product_id"] == "P01", ["order_id", "product_id", "campaign"]].head(6).to_string(index=False))


unique_promotions = promotions.drop_duplicates("product_id", keep="first")
checked = orders.merge(unique_promotions, on="product_id", how="left", validate="many_to_one")
print("去重后合并行数:", len(checked), "与订单行数一致:", len(checked) == len(orders))

try:
    orders.merge(promotions, on="product_id", how="left", validate="many_to_one")
except pd.errors.MergeError as exc:
    print("校验拦住了这次合并：", exc)


lower_customers = customers.assign(customer_id=customers["customer_id"].str.lower())
lossy = orders.merge(lower_customers, on="customer_id", how="left")
matched = int(lossy["customer_name"].notna().sum())
print("小写键匹配上的订单:", matched, "共", len(orders))
print("客户键是否唯一:", bool(customers["customer_id"].is_unique))


detail = (orders
    .merge(customers, on="customer_id", how="left", validate="many_to_one")
    .merge(products, on="product_id", how="left", validate="many_to_one"))
detail["customer_name"] = detail["customer_name"].fillna("未知客户")
detail["city"] = detail["city"].fillna("未知")
detail["revenue"] = (detail["quantity"] * detail["unit_price"]).round(2)

print("明细行数:", len(detail), "订单行数:", len(orders), "一致:", len(detail) == len(orders))
print(detail.head(4)[["order_id", "customer_name", "city", "category", "revenue"]].to_string(index=False))
print(detail.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False).to_string(index=False))
