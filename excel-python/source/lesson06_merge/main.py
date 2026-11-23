from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import pandas as pd


files = sorted(data_path("monthly").glob("sales-*.xlsx"))
print("找到文件:", [path.name for path in files])


frames = []
for path in files:
    frame = pd.read_excel(path, sheet_name="sales")
    frame["source_file"] = path.name
    frames.append(frame)
merged = pd.concat(frames, ignore_index=True)
print("合并形状:", merged.shape)
merged.head()


merged["month"] = pd.to_datetime(merged["date"]).dt.to_period("M").astype("string")
merged["amount"] = (merged["units"] * merged["price"]).round(2)
merged.groupby("month").agg(
    rows=("date", "size"),
    units=("units", "sum"),
    amount=("amount", "sum"),
).round(2)


output = Path("output")
output.mkdir(exist_ok=True)
target = output / "merged-sales.xlsx"
merged.to_excel(target, index=False, sheet_name="merged")
print("保存:", target, target.stat().st_size, "字节")
print("回读形状:", pd.read_excel(target).shape)
