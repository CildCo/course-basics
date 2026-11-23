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


import pandas as pd

REGION_MAP = {"华东": "华东", "华东区": "华东", "east": "华东", "华南": "华南", "华南区": "华南", "south": "华南", "华北": "华北", "华北区": "华北", "north": "华北"}
CATEGORY_MAP = {"办公": "办公用品", "办公用品": "办公用品", "Office": "办公用品", "OFFICE": "办公用品", "数码": "数码产品", "数码产品": "数码产品", "Digital": "数码产品"}
PRODUCT_MAP = {"笔记本": "笔记本", "Notebook": "笔记本", "notebook": "笔记本", "NOTEBOOK": "笔记本", "签字笔": "签字笔", "Pen": "签字笔", "pen": "签字笔", "文件夹": "文件夹", "Folder": "文件夹", "folder": "文件夹", "耳机": "耳机", "Headphone": "耳机", "headphone": "耳机", "显示器": "显示器", "Monitor": "显示器", "monitor": "显示器", "键盘": "键盘", "Keyboard": "键盘", "keyboard": "键盘"}
STATUS_MAP = {"已完成": "已完成", "完成": "已完成", "done": "已完成", "已取消": "已取消", "cancelled": "已取消"}

def parse_date(value):
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    if "年" in text:
        text = text.replace("年", "-").replace("月", "-").replace("日", "")
    return pd.to_datetime(text, format="mixed", dayfirst=False, errors="coerce")

def clean_orders(raw):
    df = raw.copy()
    df.columns = [column.strip().lower() for column in df.columns]

    df["order_date_raw"] = df["order_date"]
    df["order_date"] = df["order_date"].map(parse_date)
    stats = {"原始行数": len(df), "日期错误": int(df["order_date"].isna().sum())}
    df = df.dropna(subset=["order_date"])

    for column in ["order_id", "customer", "region", "category", "product", "status"]:
        df[column] = df[column].astype("string").str.strip()
    df["region"] = df["region"].map(REGION_MAP).fillna("未知")
    df["category"] = df["category"].map(CATEGORY_MAP).fillna("未知")
    df["product"] = df["product"].map(PRODUCT_MAP).fillna("未知")
    df["status"] = df["status"].map(STATUS_MAP).fillna("未知")

    stats["完全重复行"] = int(df.duplicated().sum())
    df = df.drop_duplicates()
    stats["重复订单号"] = int(df.duplicated(subset=["order_id"]).sum())
    df = df.drop_duplicates(subset=["order_id"], keep="last")

    df["customer"] = df["customer"].fillna("未知客户")
    df["unit_price"] = df["unit_price"].fillna(df.groupby("category")["unit_price"].transform("median"))

    stats["无效数量"] = int((df["units"] <= 0).sum())
    df = df[df["units"] > 0]

    invalid_price = (df["unit_price"] <= 0) | (df["unit_price"] > 5000)
    stats["异常单价"] = int(invalid_price.sum())
    valid_median = df.loc[~invalid_price].groupby("category")["unit_price"].median()
    df.loc[invalid_price, "unit_price"] = df.loc[invalid_price, "category"].map(valid_median)
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())

    df["amount"] = (df["units"].astype(float) * df["unit_price"]).round(2)
    df = df.drop(columns=["order_date_raw"]).reset_index(drop=True)
    stats["清洗后行数"] = len(df)
    stats["金额合计"] = round(float(df["amount"].sum()), 2)
    return df, stats


clean, stats = clean_orders(raw)
print("函数返回:", type(clean).__name__, "和", type(stats).__name__)
clean.head()


pd.Series(stats, name="值").to_frame()


assert clean["order_id"].is_unique, "订单号必须唯一"
assert clean[["order_date", "customer", "region", "category", "product", "status", "units", "unit_price", "amount"]].notna().all().all(), "关键列不能有缺失"
assert (clean["units"] > 0).all(), "数量必须为正"
assert ((clean["unit_price"] > 0) & (clean["unit_price"] <= 5000)).all(), "单价必须在有效范围"
print("全部断言通过")


sample = raw.sample(60, random_state=1)
sample_clean, sample_stats = clean_orders(sample)
print("抽样清洗:", len(sample), "->", len(sample_clean))
pd.Series(sample_stats, name="值").to_frame()
