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
sales["month"] = sales.index.month
sales["weekday"] = sales.index.dayofweek

monthly = sales.groupby("month")["sales"].mean()
weekday = sales.groupby("weekday")["sales"].mean()
weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

print("按月平均销售额:")
print(monthly.round(0).to_string())
print("按星期平均销售额:")
print(pd.Series(weekday.to_numpy(), index=weekday_names).round(0).to_string())


fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))

axes[0].bar(monthly.index, monthly.values, color="#6f8f9f")
axes[0].set_title("按月平均销售额")
axes[0].set_xlabel("月份")
axes[0].set_ylabel("销售额（元）")
axes[0].set_xticks(range(1, 13))

axes[1].plot(weekday_names, weekday.values, marker="o", color="#c0703a")
axes[1].set_title("按星期平均销售额")
axes[1].set_xlabel("星期")
axes[1].set_ylabel("销售额（元）")

for ax in axes:
    ax.grid(alpha=0.25)
fig.tight_layout()
path = OUTPUT / "seasonality.png"
fig.savefig(path, dpi=130)
plt.close(fig)
print("图已保存:", path.relative_to(Path.cwd()).as_posix())


pivot = sales.pivot_table(
    index="weekday", columns="month", values="sales", aggfunc="mean"
).round(0)
pivot.index = weekday_names

peak_month = int(monthly.idxmax())
peak_day = weekday_names[int(weekday.idxmax())]
print("月度峰值:", peak_month, "月")
print("星期峰值:", peak_day)
print("最高与最低月均值差:", round(monthly.max() - monthly.min(), 1), "元")
pivot
