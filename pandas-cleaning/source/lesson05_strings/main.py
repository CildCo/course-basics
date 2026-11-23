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


df = raw.copy()
for column in ["region", "category", "product", "status"]:
    df[column] = df[column].astype("string").str.strip()
df[["region", "category", "product", "status"]].head(8)


region_map = {
    "华东": "华东", "华东区": "华东", "east": "华东",
    "华南": "华南", "华南区": "华南", "south": "华南",
    "华北": "华北", "华北区": "华北", "north": "华北",
}
category_map = {
    "办公": "办公用品", "办公用品": "办公用品", "Office": "办公用品", "OFFICE": "办公用品",
    "数码": "数码产品", "数码产品": "数码产品", "Digital": "数码产品",
}
product_map = {
    "笔记本": "笔记本", "Notebook": "笔记本", "notebook": "笔记本", "NOTEBOOK": "笔记本",
    "签字笔": "签字笔", "Pen": "签字笔", "pen": "签字笔",
    "文件夹": "文件夹", "Folder": "文件夹", "folder": "文件夹",
    "耳机": "耳机", "Headphone": "耳机", "headphone": "耳机",
    "显示器": "显示器", "Monitor": "显示器", "monitor": "显示器",
    "键盘": "键盘", "Keyboard": "键盘", "keyboard": "键盘",
}
status_map = {
    "已完成": "已完成", "完成": "已完成", "done": "已完成",
    "已取消": "已取消", "cancelled": "已取消",
}

df["region"] = df["region"].map(region_map).fillna("未知")
df["category"] = df["category"].map(category_map).fillna("未知")
df["product"] = df["product"].map(product_map).fillna("未知")
df["status"] = df["status"].map(status_map).fillna("未知")
df[["region", "category", "product", "status"]].head(8)


for column in ["region", "category", "status"]:
    print(f"{column}: 归一前 {raw[column].nunique(dropna=True)} 种，归一后 {df[column].nunique(dropna=True)} 种")
df["category"].value_counts()


print("分类未映射:", int(df["category"].isna().sum()))
print("商品未映射:", int(df["product"].isna().sum()))
print("状态取值:", sorted(df["status"].unique()))
