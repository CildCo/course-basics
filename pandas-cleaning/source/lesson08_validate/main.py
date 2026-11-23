from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import pandas as pd

raw = pd.read_csv(data_path("orders_dirty.csv"), dtype={"order_id": "string"})

region_map = {"华东": "华东", "华东区": "华东", "east": "华东", "华南": "华南", "华南区": "华南", "south": "华南", "华北": "华北", "华北区": "华北", "north": "华北"}
category_map = {"办公": "办公用品", "办公用品": "办公用品", "Office": "办公用品", "OFFICE": "办公用品", "数码": "数码产品", "数码产品": "数码产品", "Digital": "数码产品"}
product_map = {"笔记本": "笔记本", "Notebook": "笔记本", "notebook": "笔记本", "NOTEBOOK": "笔记本", "签字笔": "签字笔", "Pen": "签字笔", "pen": "签字笔", "文件夹": "文件夹", "Folder": "文件夹", "folder": "文件夹", "耳机": "耳机", "Headphone": "耳机", "headphone": "耳机", "显示器": "显示器", "Monitor": "显示器", "monitor": "显示器", "键盘": "键盘", "Keyboard": "键盘", "keyboard": "键盘"}
status_map = {"已完成": "已完成", "完成": "已完成", "done": "已完成", "已取消": "已取消", "cancelled": "已取消"}

def parse_date(value):
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    if "年" in text:
        text = text.replace("年", "-").replace("月", "-").replace("日", "")
    return pd.to_datetime(text, format="mixed", dayfirst=False, errors="coerce")

df = raw.copy()
df["order_date_raw"] = df["order_date"]
df["order_date"] = df["order_date"].map(parse_date)
bad_dates = int(df["order_date"].isna().sum())
df = df.dropna(subset=["order_date"])

for column in ["region", "category", "product", "status"]:
    df[column] = df[column].astype("string").str.strip()
df["region"] = df["region"].map(region_map).fillna("未知")
df["category"] = df["category"].map(category_map).fillna("未知")
df["product"] = df["product"].map(product_map).fillna("未知")
df["status"] = df["status"].map(status_map).fillna("未知")

df["customer"] = df["customer"].fillna("未知客户")
df["unit_price"] = df["unit_price"].fillna(df.groupby("category")["unit_price"].transform("median"))

exact_dupes = int(df.duplicated().sum())
df = df.drop_duplicates()
key_dupes = int(df.duplicated(subset=["order_id"]).sum())
df = df.drop_duplicates(subset=["order_id"], keep="last")

bad_units = int((df["units"] <= 0).sum())
df = df[df["units"] > 0]

invalid_price = (df["unit_price"] <= 0) | (df["unit_price"] > 5000)
bad_prices = int(invalid_price.sum())
valid_median = df.loc[~invalid_price].groupby("category")["unit_price"].median()
df.loc[invalid_price, "unit_price"] = df.loc[invalid_price, "category"].map(valid_median)
df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
df["amount"] = (df["units"].astype(float) * df["unit_price"]).round(2)
df = df.reset_index(drop=True)

print("原始行数:", len(raw))
print("日期错误:", bad_dates, "完全重复:", exact_dupes, "订单号重复:", key_dupes)
print("无效数量:", bad_units, "异常单价:", bad_prices)
print("清洗后行数:", len(df))
df.head()


before_region = raw.groupby("region", dropna=False).size().rename("清洗前")
after_region = df.groupby("region").size().rename("清洗后")
region_check = pd.concat([before_region, after_region], axis=1).fillna(0).astype(int)
region_check


before_status = raw["status"].fillna("空值").value_counts().rename("清洗前")
after_status = df["status"].value_counts().rename("清洗后")
status_check = pd.concat([before_status, after_status], axis=1).fillna(0).astype(int)
status_check


raw_amount = (raw["units"].clip(lower=0) * raw["unit_price"].fillna(0)).sum()
clean_amount = df["amount"].sum()
print(f"清洗前金额合计: {raw_amount:,.2f}")
print(f"清洗后金额合计: {clean_amount:,.2f}")
print(f"差额: {clean_amount - raw_amount:,.2f}")


by_category = df.groupby("category").agg(
    orders=("order_id", "nunique"),
    units=("units", "sum"),
    amount=("amount", "sum"),
).round(2).sort_values("amount", ascending=False)
by_category
