from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

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


raw = pd.read_csv(data_path("orders_dirty.csv"), dtype={"order_id": "string"})
clean, stats = clean_orders(raw)

before = {
    "行数": len(raw),
    "列数": raw.shape[1],
    "缺失单元格": int(raw.isna().sum().sum()),
    "完全重复行": int(raw.duplicated().sum()),
    "重复订单号": int(raw.duplicated(subset=["order_id"]).sum()),
    "日期写法": int(raw["order_date"].astype("string").str.replace(r"\d", "9", regex=True).nunique(dropna=True)),
    "金额合计": round(float((raw["units"].clip(lower=0) * raw["unit_price"].fillna(0)).sum()), 2),
}
after = {
    "行数": len(clean),
    "列数": clean.shape[1],
    "缺失单元格": int(clean.isna().sum().sum()),
    "完全重复行": int(clean.duplicated().sum()),
    "重复订单号": int(clean.duplicated(subset=["order_id"]).sum()),
    "日期写法": int(clean["order_date"].dt.strftime("%Y-%m-%d").str.replace(r"\d", "9", regex=True).nunique()),
    "金额合计": round(float(clean["amount"].sum()), 2),
}
comparison = pd.DataFrame({"清洗前": before, "清洗后": after})
comparison


output = Path("output")
output.mkdir(exist_ok=True)

clean_path = output / "clean_orders.csv"
summary_path = output / "cleaning-summary.csv"
clean.to_csv(clean_path, index=False, encoding="utf-8")
comparison.to_csv(summary_path, encoding="utf-8")
print("已写入:", clean_path, f"({clean_path.stat().st_size} 字节)")
print("已写入:", summary_path, f"({summary_path.stat().st_size} 字节)")


print("清洗结论")
print(f"- 原始 {len(raw)} 行，清洗后 {len(clean)} 行，保留 {len(clean) / len(raw):.1%}。")
print(f"- 日期错误 {stats['日期错误']} 行，完全重复 {stats['完全重复行']} 行，重复订单号 {stats['重复订单号']} 行。")
print(f"- 无效数量 {stats['无效数量']} 行已删除，异常单价 {stats['异常单价']} 行已按分类中位数修正。")
print(f"- 清洗后订单号唯一：{clean['order_id'].is_unique}，关键列无缺失：{bool(clean.notna().all().all())}。")
print(f"- 清洗后覆盖 {clean['order_date'].min().date()} 到 {clean['order_date'].max().date()}，金额合计 {clean['amount'].sum():,.2f} 元。")


check = pd.read_csv(clean_path, dtype={"order_id": "string"})
print("回读形状:", check.shape)
print("回读订单号唯一:", check["order_id"].is_unique)
print("回读缺失总数:", int(check.isna().sum().sum()))
print("输出目录:", sorted(path.name for path in output.glob("*")))
