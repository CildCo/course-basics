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
frames = [pd.read_excel(path, sheet_name="sales") for path in files]
merged = pd.concat(frames, ignore_index=True)
merged["month"] = pd.to_datetime(merged["date"]).dt.to_period("M").astype("string")
merged["amount"] = (merged["units"] * merged["price"]).round(2)
print("总行数:", len(merged), "月份:", sorted(merged["month"].unique()))


summary = merged.groupby("month").agg(
    rows=("date", "size"),
    units=("units", "sum"),
    amount=("amount", "sum"),
).round(2).reset_index()
summary


output = Path("output") / "reports"
output.mkdir(parents=True, exist_ok=True)
paths = []
for month, part in merged.groupby("month"):
    target = output / f"sales-{month}-report.xlsx"
    category = part.groupby("category").agg(
        rows=("date", "size"),
        units=("units", "sum"),
        amount=("amount", "sum"),
    ).round(2).reset_index()
    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        part.to_excel(writer, sheet_name="明细", index=False)
        category.to_excel(writer, sheet_name="分类汇总", index=False)
    paths.append(target)
print("生成文件:", [path.name for path in paths])


for path in paths:
    book = pd.read_excel(path, sheet_name=None)
    print(path.name, {name: frame.shape for name, frame in book.items()})


one = pd.read_excel(paths[0], sheet_name="分类汇总")
one
