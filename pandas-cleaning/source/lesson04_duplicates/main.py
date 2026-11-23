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
print("原始行数:", len(raw))


print("完全重复行:", int(raw.duplicated().sum()))
print("涉及重复订单号的行:", int(raw.duplicated(subset=["order_id"], keep=False).sum()))
print("重复订单号个数:", int(raw.loc[raw.duplicated(subset=["order_id"], keep=False), "order_id"].nunique()))


exact = raw[raw.duplicated()]
same_id = raw[raw.duplicated(subset=["order_id"], keep=False)].sort_values("order_id")
print("完全重复示例:")
print(exact[["order_id", "order_date", "units", "status"]].head().to_string())
print("\n同号不同内容示例:")
same_id[["order_id", "order_date", "units", "status"]].head(10)


df = raw.drop_duplicates().copy()
print("去掉完全重复后:", len(df))
df = df.drop_duplicates(subset=["order_id"], keep="last")
print("按订单号保留最后一条:", len(df))
print("订单号唯一:", df["order_id"].is_unique)


duplicated_ids = raw.loc[raw.duplicated(subset=["order_id"], keep=False), "order_id"].unique()
sample_id = duplicated_ids[0]
print("示例订单号:", sample_id)
raw[raw["order_id"] == sample_id][["order_id", "order_date", "units", "unit_price", "status"]]
