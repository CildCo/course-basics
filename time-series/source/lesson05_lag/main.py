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
sales["lag1"] = sales["sales"].shift(1)
sales["lag7"] = sales["sales"].shift(7)
sales["diff1"] = sales["sales"].diff()

print(sales[["sales", "lag1", "lag7", "diff1"]].tail(5).to_string())
print("lag1 缺失数:", int(sales["lag1"].isna().sum()))


series = sales["sales"]
rows = []
for lag in range(1, 15):
    rows.append(
        {
            "lag": lag,
            "手算": round(series.corr(series.shift(lag)), 3),
            "pandas": round(series.autocorr(lag), 3),
        }
    )
acf = pd.DataFrame(rows)
print("前 5 个滞后:")
print(acf.head(5).to_string(index=False))
print("相关性最强的滞后:", int(acf.loc[acf["手算"].abs().idxmax(), "lag"]))
acf


fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(acf["lag"], acf["手算"], color="#5f7f8f")
ax.axhline(0, color="#333333", linewidth=0.8)
ax.set_title("销售额自相关（滞后 1-14 天）")
ax.set_xlabel("滞后天数")
ax.set_ylabel("相关系数")
ax.set_xticks(acf["lag"])
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
path = OUTPUT / "acf.png"
fig.savefig(path, dpi=130)
plt.close(fig)
print("图已保存:", path.relative_to(Path.cwd()).as_posix())
