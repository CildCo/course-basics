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

sales = pd.read_csv(
    data_path("sales_export.csv"),
    dtype={"customer_id": "string", "product_id": "string"},
)
customers = pd.read_csv(data_path("customers.csv"), dtype={"customer_id": "string"})
products = pd.read_csv(data_path("products.csv"), dtype={"product_id": "string"})
returns = pd.read_csv(data_path("returns.csv"), parse_dates=["return_date"])

print("导出订单:", sales.shape)
print("客户:", customers.shape, "商品:", products.shape, "退货:", returns.shape)
print(sales.head(4).to_string(index=False))
print("重复订单行:", int(sales.duplicated("order_id").sum()))


clean = sales.copy()
clean.columns = [column.strip().lower() for column in clean.columns]
for column in ["order_id", "product_id", "channel"]:
    clean[column] = clean[column].astype("string").str.strip()
clean["customer_id"] = clean["customer_id"].str.strip()
clean["order_date"] = pd.to_datetime(clean["order_date"], format="mixed")
clean = clean.drop_duplicates(subset="order_id", keep="last")

print("原始行数:", len(sales), "清洗后:", len(clean))
print(clean.dtypes.to_string())
print(clean.head(3).to_string(index=False))


missing_price = clean["unit_price"].isna()
price_map = products.set_index("product_id")["list_price"]
clean.loc[missing_price, "unit_price"] = clean.loc[missing_price, "product_id"].map(price_map)
clean["unit_price"] = clean["unit_price"].astype("float")

print("补价行数:", int(missing_price.sum()))
print("单价缺失剩余:", int(clean["unit_price"].isna().sum()))
print(clean.loc[missing_price, ["order_id", "product_id", "unit_price"]].to_string(index=False))


detail = (clean
    .merge(customers, on="customer_id", how="left", validate="many_to_one", indicator="customer_match")
    .merge(products[["product_id", "product_name", "category"]], on="product_id", how="left", validate="many_to_one"))
detail["customer_name"] = detail["customer_name"].fillna("未知客户")
detail["city"] = detail["city"].fillna("未知")
detail["segment"] = detail["segment"].fillna("未知")
detail["revenue"] = (detail["quantity"] * detail["unit_price"]).round(2)

print("明细行数:", len(detail), "唯一订单:", detail["order_id"].nunique())
print(detail["customer_match"].value_counts().to_string())
print("品类缺失:", int(detail["category"].isna().sum()))
print(detail.head(3)[["order_id", "customer_name", "city", "category", "revenue"]].to_string(index=False))


refund = returns.groupby("order_id", as_index=False)["refund_amount"].sum()
detail = detail.merge(refund, on="order_id", how="left", validate="many_to_one")
detail["refund_amount"] = detail["refund_amount"].fillna(0.0)
detail["net_revenue"] = (detail["revenue"] - detail["refund_amount"]).round(2)

print(f"退货订单数: {int((detail['refund_amount'] > 0).sum())}")
print(f"销售额: {detail['revenue'].sum():.2f}")
print(f"退款: {detail['refund_amount'].sum():.2f}")
print(f"净收入: {detail['net_revenue'].sum():.2f}")


monthly_pivot = (detail
    .assign(month=detail["order_date"].dt.to_period("M").astype(str))
    .pivot_table(index="month", columns="category", values="net_revenue", aggfunc="sum", fill_value=0)
    .round(0))
print("月度净收入：")
print(monthly_pivot.to_string())

city_report = (detail.groupby("city", as_index=False)
    .agg(net_revenue=("net_revenue", "sum"), orders=("order_id", "nunique"), customers=("customer_id", "nunique"))
    .sort_values("net_revenue", ascending=False))
city_report["share"] = (city_report["net_revenue"] / city_report["net_revenue"].sum()).round(3)
print("\n城市贡献：")
print(city_report.to_string(index=False))


fig, ax = plt.subplots(figsize=(9, 4.5))
monthly_pivot.plot(
    kind="bar",
    stacked=True,
    ax=ax,
    color=["#8FB8CC", "#4F86A6", "#2F5F7A", "#D9A566"],
    width=0.72,
)
ax.set_title("2025 年按月净收入（按品类堆叠）")
ax.set_xlabel("月份")
ax.set_ylabel("净收入（元）")
ax.tick_params(axis="x", rotation=0)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(title="品类", frameon=False, ncol=4, loc="upper left")
fig.tight_layout()
fig.savefig(out / "project-report.png", dpi=120)
display(Image(filename=str(out / "project-report.png")))
plt.close(fig)
print("月度表形状:", monthly_pivot.shape)


checks = pd.DataFrame([
    {"检查项": "订单主键唯一", "结果": bool(detail["order_id"].is_unique)},
    {"检查项": "净收入无缺失", "结果": bool(detail["net_revenue"].notna().all())},
    {"检查项": "品类全部匹配", "结果": bool(detail["category"].notna().all())},
    {"检查项": "退款不超过销售额", "结果": bool((detail["refund_amount"] <= detail["revenue"]).all())},
])
print(checks.to_string(index=False))

top_category = detail.groupby("category")["net_revenue"].sum().idxmax()
top_city = city_report.iloc[0]["city"]
summary_text = (
    f"订单数：{int(detail['order_id'].nunique())}\n"
    f"销售额：{detail['revenue'].sum():.2f} 元\n"
    f"退款：{detail['refund_amount'].sum():.2f} 元\n"
    f"净收入：{detail['net_revenue'].sum():.2f} 元\n"
    f"净收入最高品类：{top_category}\n"
    f"净收入最高城市：{top_city}\n"
)
print("\n" + summary_text)


detail.to_csv(out / "clean_sales.csv", index=False, encoding="utf-8-sig")
monthly_pivot.to_csv(out / "report_monthly.csv", encoding="utf-8-sig")
city_report.to_csv(out / "report_city.csv", index=False, encoding="utf-8-sig")
(out / "summary.txt").write_text(summary_text, encoding="utf-8")

print("导出文件:", [path.name for path in sorted(out.glob("report_*"))])
print("明细列数:", detail.shape[1], "月份数:", monthly_pivot.shape[0])
