from pathlib import Path

import numpy as np

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

customers = pd.read_csv(data_path("customers.csv"))
print("原始类型：")
print(customers.dtypes.to_string())

dirty = pd.Series([" 北京 ", "上海", " 广州", "深圳 "])
print("\n原始值:", dirty.tolist())
print("去空格:", dirty.str.strip().tolist())


customers["name_len"] = customers["customer_name"].str.len()
customers["is_enterprise"] = customers["segment"].str.contains("企业")
print(customers.head(5)[["customer_name", "city", "segment", "name_len", "is_enterprise"]].to_string(index=False))

codes = pd.Series(["BJ-01", "SH-02", "GZ-03", "SZ-04"])
parts = codes.str.split("-", expand=True)
parts.columns = ["city_code", "store_no"]
parts["city_name"] = parts["city_code"].map({"BJ": "北京", "SH": "上海", "GZ": "广州", "SZ": "深圳"})
print("\n拆分编号：")
print(parts.to_string(index=False))
print("门店号是否都为数字:", bool(parts["store_no"].str.isdigit().all()))


rng = np.random.default_rng(7)
big_city = pd.Series(rng.choice(["北京", "上海", "广州", "深圳", "杭州", "成都"], size=10000))
big_category = big_city.astype("category")

print("object 内存（字节）:", int(big_city.memory_usage(deep=True)))
print("category 内存（字节）:", int(big_category.memory_usage(deep=True)))
print("类别数:", big_category.cat.categories.size)

customers["segment_ordered"] = pd.Categorical(
    customers["segment"],
    categories=["个人", "企业"],
    ordered=True,
)
print("\n按客群顺序排序：")
print(customers.sort_values("segment_ordered")[["customer_name", "segment_ordered"]].head(4).to_string(index=False))
print("类别顺序:", customers["segment_ordered"].cat.categories.tolist())


raw = pd.DataFrame({
    "order_id": ["O1", "O2", "O3", "O4"],
    "quantity": [2, None, 5, 1],
    "paid": [True, False, None, True],
    "note": ["加急", None, "礼品包装", ""],
})
print("转换前：")
print(raw.dtypes.to_string())

typed = raw.convert_dtypes()
print("\n转换后：")
print(typed.dtypes.to_string())
print(typed.to_string(index=False))


print("数量合计:", typed["quantity"].sum())
print("缺失数量:", int(typed["quantity"].isna().sum()))
print("缺失布尔值:", typed.loc[2, "paid"], "类型:", type(typed.loc[2, "paid"]).__name__)

filled = typed["quantity"].fillna(0).astype("int64")
print("填充后 dtype:", filled.dtype, "合计:", int(filled.sum()))
print("备注去空格:", typed["note"].str.strip().fillna("").tolist())
