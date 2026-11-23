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


patterns = raw["order_date"].astype("string").str.replace(r"\d", "9", regex=True)
patterns.value_counts(dropna=False)


parsed = pd.to_datetime(raw["order_date"], format="mixed", errors="coerce")
print("直接解析失败:", int(parsed.isna().sum()), "行")
parsed.head(10)


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
print("解析失败:", int(df["order_date"].isna().sum()), "行")
df[["order_date_raw", "order_date"]].head(8)


bad = df[df["order_date"].isna()][["order_id", "order_date_raw"]]
print("错误日期:")
print(bad.to_string(index=False))


valid = df.dropna(subset=["order_date"]).copy()
valid["month"] = valid["order_date"].dt.to_period("M").astype("string")
print("日期范围:", valid["order_date"].min().date(), "到", valid["order_date"].max().date())
print("按月行数:")
print(valid.groupby("month").size().to_string())
