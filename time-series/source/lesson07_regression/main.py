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

frame = sales.copy()
frame["lag1"] = frame["sales"].shift(1)
frame["lag7"] = frame["sales"].shift(7)
frame["lag14"] = frame["sales"].shift(14)
frame["weekday"] = frame.index.dayofweek
frame["month"] = frame.index.month
frame = frame.dropna(subset=["lag1", "lag7", "lag14"])

features = ["lag1", "lag7", "lag14", "weekday", "month"]
horizon = 60
train = frame.iloc[:-horizon]
test = frame.iloc[-horizon:]

def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    return round(mae, 1), round(rmse, 1)

print("补齐后:", len(sales), "天")
print("建模样本:", len(frame), "行")
print("训练:", len(train), "天，测试:", len(test), "天")
print("特征:", features)


from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(train[features], train["sales"])

history = train["sales"].astype(float).tolist()
predictions = []
for date in test.index:
    row = {
        "lag1": history[-1],
        "lag7": history[-7],
        "lag14": history[-14],
        "weekday": date.dayofweek,
        "month": date.month,
    }
    value = float(model.predict(pd.DataFrame([row]))[0])
    predictions.append(value)
    history.append(value)

print("完成", len(predictions), "天递归预测")
print("预测区间:", test.index.min().date(), "至", test.index.max().date())


last_value = float(train["sales"].iloc[-1])
naive_pred = [last_value] * horizon
history = train["sales"].astype(float).tolist()
seasonal_pred = []
for _ in range(horizon):
    seasonal_pred.append(history[-7])
    history.append(history[-7])

rows = []
for name, pred in [
    ("naive", naive_pred),
    ("seasonal naive", seasonal_pred),
    ("线性回归", predictions),
]:
    mae, rmse = metrics(test["sales"], pred)
    rows.append({"模型": name, "MAE": mae, "RMSE": rmse})
comparison = pd.DataFrame(rows)
print(comparison.to_string(index=False))

coef = pd.DataFrame({"特征": features, "系数": model.coef_})
coef["绝对值"] = coef["系数"].abs()
print("回归系数:")
print(coef.sort_values("绝对值", ascending=False).drop(columns="绝对值").round(3).to_string(index=False))
print("截距:", round(model.intercept_, 2))


fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(test.index, test["sales"], color="#333333", linewidth=1.2, label="实际")
ax.plot(test.index, predictions, color="#2f6f8f", linewidth=1.6, label="线性回归")
ax.plot(test.index, seasonal_pred, color="#c0703a", linestyle="--", label="seasonal naive")
ax.set_title("线性回归与季节性基线的预测对比")
ax.set_xlabel("日期")
ax.set_ylabel("销售额（元）")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
path = OUTPUT / "regression.png"
fig.savefig(path, dpi=130)
plt.close(fig)
print("图已保存:", path.relative_to(Path.cwd()).as_posix())
