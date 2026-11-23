from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import pandas as pd


sales = pd.read_excel(data_path("sales.xlsx"), sheet_name="sales")
print("形状:", sales.shape)
sales.head()


book = pd.read_excel(data_path("sales.xlsx"), sheet_name=None)
print({name: frame.shape for name, frame in book.items()})


subset = pd.read_excel(
    data_path("sales.xlsx"),
    sheet_name="sales",
    usecols=["date", "region", "product", "units", "price"],
    dtype={"units": "Int64", "price": "float64"},
)
print(subset.shape)
subset.dtypes


output = Path("output")
output.mkdir(exist_ok=True)
january = sales[pd.to_datetime(sales["date"]).dt.month == 1]
target = output / "january-sales.xlsx"
january.to_excel(target, index=False, sheet_name="sales")
print("写入:", target, "行数:", len(january))
pd.read_excel(target).head(3)
