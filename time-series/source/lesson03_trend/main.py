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
sales["ma7"] = sales["sales"].rolling(7).mean()
sales["ma30"] = sales["sales"].rolling(30).mean()
sales["std30"] = sales["sales"].rolling(30).std()

print("最近 5 天:")
print(sales[["sales", "ma7", "ma30", "std30"]].tail(5).round(1).to_string())
print("前 6 天的 7 日均线为空:", bool(sales["ma7"].head(6).isna().all()))


fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(sales.index, sales["sales"], color="#a7b1bd", linewidth=0.8, label="日销售额")
ax.plot(sales.index, sales["ma7"], color="#2f6f8f", linewidth=1.6, label="7 日移动平均")
ax.plot(sales.index, sales["ma30"], color="#c0703a", linewidth=1.8, label="30 日移动平均")
ax.set_title("日销售额与移动平均")
ax.set_xlabel("日期")
ax.set_ylabel("销售额（元）")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
path = OUTPUT / "trend.png"
fig.savefig(path, dpi=130)
plt.close(fig)
print("图已保存:", path.relative_to(Path.cwd()).as_posix())


latest = sales.iloc[-1]
print("最新一天:", sales.index[-1].date())
print("销售额:", int(latest["sales"]))
print("7 日均线:", round(latest["ma7"], 1))
print("30 日均线:", round(latest["ma30"], 1))
print("30 日波动（标准差）:", round(latest["std30"], 1))
peak = sales["ma30"].idxmax()
print("30 日均线最高出现在:", peak.date(), "，值为", round(sales.loc[peak, "ma30"], 1))
