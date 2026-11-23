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
full = sales.reindex(full_index)
full[["sales", "orders"]] = full[["sales", "orders"]].interpolate().round()

frame = full.copy()
frame["lag1"] = frame["sales"].shift(1)
frame["lag7"] = frame["sales"].shift(7)
frame["lag14"] = frame["sales"].shift(14)
frame["lag28"] = frame["sales"].shift(28)
frame["rolling7"] = frame["sales"].shift(1).rolling(7).mean()
frame["weekday"] = frame.index.dayofweek
frame["month"] = frame.index.month
frame["trend"] = (frame.index - frame.index.min()).days
day_of_year = frame.index.dayofyear
frame["sin1"] = np.sin(2 * np.pi * day_of_year / 365.25)
frame["cos1"] = np.cos(2 * np.pi * day_of_year / 365.25)
frame["sin2"] = np.sin(4 * np.pi * day_of_year / 365.25)
frame["cos2"] = np.cos(4 * np.pi * day_of_year / 365.25)
frame = frame.dropna()

features = [
    "lag1", "lag7", "lag14", "lag28", "rolling7", "weekday", "month",
    "trend", "sin1", "cos1", "sin2", "cos2",
]
horizon = 90
train = frame.iloc[:-horizon]
test = frame.iloc[-horizon:]

print("补齐后:", len(full), "天")
print("建模样本:", len(frame), "行")
print("训练:", len(train), "天，测试:", len(test), "天")
print("测试区间:", test.index.min().date(), "至", test.index.max().date())


from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

models = {
    "线性回归": LinearRegression(),
    "随机森林": RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=1,
    ),
}

start_date = frame.index.min()
predictions_by_model = {}
for name, model in models.items():
    model.fit(train[features], train["sales"])
    history = train["sales"].astype(float).tolist()
    predictions = []
    for date in test.index:
        day = date.dayofyear
        row = {
            "lag1": history[-1],
            "lag7": history[-7],
            "lag14": history[-14],
            "lag28": history[-28],
            "rolling7": float(np.mean(history[-7:])),
            "weekday": date.dayofweek,
            "month": date.month,
            "trend": float((date - start_date).days),
            "sin1": float(np.sin(2 * np.pi * day / 365.25)),
            "cos1": float(np.cos(2 * np.pi * day / 365.25)),
            "sin2": float(np.sin(4 * np.pi * day / 365.25)),
            "cos2": float(np.cos(4 * np.pi * day / 365.25)),
        }
        value = float(model.predict(pd.DataFrame([row]))[0])
        predictions.append(value)
        history.append(value)
    predictions_by_model[name] = predictions
    print(name, "完成", len(predictions), "天预测，最后一天", round(predictions[-1], 1))


def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    return round(mae, 1), round(rmse, 1)

history = train["sales"].astype(float).tolist()
seasonal_pred = []
for _ in range(horizon):
    seasonal_pred.append(history[-7])
    history.append(history[-7])

rows = []
seasonal_mae, seasonal_rmse = metrics(test["sales"], seasonal_pred)
rows.append({"模型": "seasonal naive", "MAE": seasonal_mae, "RMSE": seasonal_rmse})
for name, pred in predictions_by_model.items():
    mae, rmse = metrics(test["sales"], pred)
    rows.append({"模型": name, "MAE": mae, "RMSE": rmse})
comparison = pd.DataFrame(rows)

report_dir = OUTPUT / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
report_path = report_dir / "metrics.csv"
comparison.to_csv(report_path, index=False)

linear_model = models["线性回归"]
coef = pd.DataFrame({"特征": features, "系数": linear_model.coef_})
coef["绝对值"] = coef["系数"].abs()
print(comparison.to_string(index=False))
print("线性回归系数:")
print(coef.sort_values("绝对值", ascending=False).drop(columns="绝对值").round(3).to_string(index=False))
print("评估文件:", report_path.relative_to(Path.cwd()).as_posix())


best_name = (
    comparison[comparison["模型"] != "seasonal naive"]
    .sort_values("RMSE")
    .iloc[0]["模型"]
)
best_pred = predictions_by_model[best_name]

fig, ax = plt.subplots(figsize=(12, 4.8))
history_window = 180
history_part = train["sales"].iloc[-history_window:]
ax.plot(history_part.index, history_part, color="#7f8c99", linewidth=1.0, label="历史销售额")
ax.plot(test.index, test["sales"], color="#333333", linewidth=1.2, label="实际")
ax.plot(test.index, seasonal_pred, color="#c0703a", linestyle="--", label="seasonal naive")
ax.plot(test.index, predictions_by_model["线性回归"], color="#2f6f8f", linewidth=1.6, label="线性回归")
ax.plot(test.index, predictions_by_model["随机森林"], color="#7a9a6f", linewidth=1.2, label="随机森林")
ax.set_title("最后 90 天销售预测")
ax.set_xlabel("日期")
ax.set_ylabel("销售额（元）")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
forecast_path = OUTPUT / "forecast.png"
fig.savefig(forecast_path, dpi=130)
plt.close(fig)

actual = test["sales"].astype(float).to_numpy()
residual = actual - np.asarray(best_pred)
baseline_rmse = metrics(test["sales"], seasonal_pred)[1]
model_rmse = metrics(test["sales"], best_pred)[1]
improvement = (baseline_rmse - model_rmse) / baseline_rmse * 100
print("图已保存:", forecast_path.relative_to(Path.cwd()).as_posix())
print("平均残差:", round(float(residual.mean()), 1))
print("最大高估:", round(float(residual.min()), 1))
print("最大低估:", round(float(residual.max()), 1))
print(f"最佳模型: {best_name}")
print(f"相对季节基线的 RMSE 改善: {improvement:.1f}%")
print(
    f"结论：未来 {horizon} 天平均预测销售额 {np.mean(best_pred):,.1f} 元，"
    f"{best_name} 的 RMSE 为 {model_rmse}，基线为 {baseline_rmse}。"
)
