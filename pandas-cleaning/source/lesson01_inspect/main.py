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
print("行数:", raw.shape[0], "列数:", raw.shape[1])
raw.head()


missing = raw.isna().sum()
print("缺失值总数:", int(missing.sum()))
print(missing[missing > 0].to_string())
print("完全重复行:", int(raw.duplicated().sum()))
print("重复订单号:", int(raw.duplicated(subset=["order_id"]).sum()))


for column in ["region", "category", "status"]:
    print(f"\n{column}:")
    print(raw[column].value_counts(dropna=False).to_string())


patterns = raw["order_date"].astype("string").str.replace(r"\d", "9", regex=True)
print("日期写法:")
print(patterns.value_counts(dropna=False).to_string())
print("\n数量与单价:")
raw[["units", "unit_price"]].describe().round(2)


checklist = pd.DataFrame([
    {"检查项": "缺失值", "发现": int(missing.sum()), "下一步": "按业务含义填充或删除"},
    {"检查项": "完全重复行", "发现": int(raw.duplicated().sum()), "下一步": "去重"},
    {"检查项": "重复订单号", "发现": int(raw.duplicated(subset=["order_id"]).sum()), "下一步": "按更新时间保留一条"},
    {"检查项": "日期写法", "发现": int(patterns.nunique()), "下一步": "统一解析为日期"},
    {"检查项": "区域/分类写法", "发现": raw["region"].nunique() + raw["category"].nunique(), "下一步": "建立别名映射"},
    {"检查项": "异常数值", "发现": int(((raw["units"] <= 0) | (raw["unit_price"] <= 0)).sum()), "下一步": "按业务规则修正"},
])
checklist
