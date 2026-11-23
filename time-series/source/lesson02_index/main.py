from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

def load_sales():
    frame = pd.read_csv(data_path("daily_sales.csv"), parse_dates=["date"])
    return frame.sort_values("date").reset_index(drop=True)

OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)
print("pandas", pd.__version__, "numpy", np.__version__)
print("工作目录就绪")

sales = load_sales().set_index("date")
print("索引类型:", type(sales.index).__name__)
print("是否 DatetimeIndex:", isinstance(sales.index, pd.DatetimeIndex))
print(sales.head(3).to_string())


full_index = pd.date_range(sales.index.min(), sales.index.max(), freq="D")
missing = full_index.difference(sales.index)
print("完整日历:", len(full_index), "天")
print("实际记录:", len(sales), "天")
print("缺失:", len(missing), "天")
print([day.strftime("%Y-%m-%d") for day in missing])


full = sales.reindex(full_index)
print("补齐前的缺失值:")
print(full.isna().sum().to_string())

full["sales"] = full["sales"].interpolate().round().astype(int)
full["orders"] = full["orders"].interpolate().round().astype(int)
print("补齐后缺失值:", int(full.isna().sum().sum()))
print(full.loc[missing].to_string())


weekly = full["sales"].resample("W").sum()
monthly = full["sales"].resample("ME").sum()
print("周合计（最后 3 周）:")
print(weekly.tail(3).to_string())
print("月合计（最后 3 月）:")
print(monthly.tail(3).to_string())
print("周合计行数:", len(weekly), "月合计行数:", len(monthly))
