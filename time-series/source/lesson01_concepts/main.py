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

sales = load_sales()
print("数据:", len(sales), "行")
print("日期范围:", sales["date"].min().date(), "至", sales["date"].max().date())
print(sales.head(3).to_string(index=False))


print("原始日期是否递增:", sales["date"].is_monotonic_increasing)

shuffled = sales.sample(frac=1.0, random_state=7).reset_index(drop=True)
print("打乱后前 3 行:")
print(shuffled.head(3).to_string(index=False))
print("打乱后日期是否递增:", shuffled["date"].is_monotonic_increasing)


last_60 = sales.tail(60)
random_60 = sales.sample(60, random_state=7)
print("最后 60 天平均销售:", round(last_60["sales"].mean(), 1))
print("随机 60 天平均销售:", round(random_60["sales"].mean(), 1))

in_order = sales["sales"].corr(sales["sales"].shift(1))
after_shuffle = shuffled["sales"].corr(shuffled["sales"].shift(1))
print("按时间顺序 lag-1 相关:", round(in_order, 3))
print("打乱后 lag-1 相关:", round(after_shuffle, 3))
