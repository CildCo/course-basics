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
full_index = pd.date_range(sales.index.min(), sales.index.max(), freq="D")
sales = sales.reindex(full_index)
sales[["sales", "orders"]] = sales[["sales", "orders"]].interpolate().round()

horizon = 60
train = sales.iloc[:-horizon]
test = sales.iloc[-horizon:]

def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    return round(mae, 1), round(rmse, 1)

print("补齐后:", len(sales), "天")
print("训练:", len(train), "天", train.index.min().date(), "至", train.index.max().date())
print("测试:", len(test), "天", test.index.min().date(), "至", test.index.max().date())


last_value = float(train["sales"].iloc[-1])
naive_pred = [last_value] * horizon

history = train["sales"].astype(float).tolist()
seasonal_pred = []
for _ in range(horizon):
    value = history[-7]
    seasonal_pred.append(value)
    history.append(value)

rows = []
for name, pred in [("naive（昨天）", naive_pred), ("seasonal naive（上周同日）", seasonal_pred)]:
    mae, rmse = metrics(test["sales"], pred)
    rows.append({"模型": name, "MAE": mae, "RMSE": rmse})
result = pd.DataFrame(rows)
print(result.to_string(index=False))


fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(test.index, test["sales"], color="#333333", linewidth=1.2, label="实际")
ax.plot(test.index, naive_pred, color="#9aa5b1", linestyle="--", label="naive")
ax.plot(test.index, seasonal_pred, color="#c0703a", linewidth=1.5, label="seasonal naive")
ax.set_title("测试集上的基线预测")
ax.set_xlabel("日期")
ax.set_ylabel("销售额（元）")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
path = OUTPUT / "baseline.png"
fig.savefig(path, dpi=130)
plt.close(fig)
print("图已保存:", path.relative_to(Path.cwd()).as_posix())
