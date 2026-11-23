from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

SEED = 42
np.random.seed(SEED)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

SNAPSHOT = pd.Timestamp("2025-06-30")

df = pd.read_csv(data_path("customer_churn.csv"), parse_dates=["signup_date"])
df["support_notes"] = df["support_notes"].fillna("")
df["signup_month"] = df["signup_date"].dt.month
df["signup_weekday"] = df["signup_date"].dt.weekday
df["is_weekend"] = (df["signup_weekday"] >= 5).astype(int)
df["tenure_days"] = (SNAPSHOT - df["signup_date"]).dt.days

display(df[["signup_date", "signup_month", "signup_weekday", "is_weekend", "tenure_days"]].head(5))
print("观察截止日:", SNAPSHOT.date())
print("账龄天数范围:", int(df["tenure_days"].min()), "到", int(df["tenure_days"].max()))


usage = pd.read_csv(data_path("usage_monthly.csv"), parse_dates=["month"])
print("月度记录:", len(usage), "客户数:", usage["customer_id"].nunique())
print("月份:", ", ".join(usage["month"].dt.strftime("%Y-%m").unique()))

agg = usage.groupby("customer_id").agg(
    usage_mean_6m=("usage_gb", "mean"),
    usage_std_6m=("usage_gb", "std"),
    usage_max_6m=("usage_gb", "max"),
    active_months=("usage_gb", "count"),
).reset_index()

pivot = usage.pivot(index="customer_id", columns="month", values="usage_gb").sort_index(axis=1)
first_half = pivot.iloc[:, :3].mean(axis=1)
last_half = pivot.iloc[:, -3:].mean(axis=1)
trend = (last_half / first_half - 1).rename("usage_trend").reset_index()
agg = agg.merge(trend, on="customer_id")

data = df.merge(agg, on="customer_id", how="left")
print("合并后客户数:", len(data))
print("趋势缺失:", int(data["usage_trend"].isna().sum()))
display(data[["customer_id", "usage_mean_6m", "usage_std_6m", "usage_trend", "active_months"]].head(4))


fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))

churn_ids = data.loc[data["churned"] == 1, "customer_id"].head(3)
stay_ids = data.loc[data["churned"] == 0, "customer_id"].head(3)
for cid in stay_ids:
    rows = usage[usage["customer_id"] == cid].sort_values("month")
    axes[0].plot(rows["month"], rows["usage_gb"], marker="o", color="#4C78A8", alpha=0.7)
for cid in churn_ids:
    rows = usage[usage["customer_id"] == cid].sort_values("month")
    axes[0].plot(rows["month"], rows["usage_gb"], marker="o", color="#C44E52", alpha=0.7)
axes[0].set_title("蓝：留存客户 / 红：流失客户")
axes[0].set_ylabel("月用量（GB）")
axes[0].tick_params(axis="x", rotation=30)
axes[0].grid(alpha=0.3)
axes[0].spines[["top", "right"]].set_visible(False)

trend_bins = pd.qcut(data["usage_trend"], q=4, labels=["下降最快", "偏下降", "偏上升", "上升最快"])
trend_stats = data.assign(trend_bin=trend_bins).groupby("trend_bin", observed=True)["churned"].mean() * 100
axes[1].bar(trend_stats.index.astype(str), trend_stats.values, color="#6B9E8A")
axes[1].set_title("按用量趋势分组的流失率")
axes[1].set_ylabel("流失率（%）")
axes[1].tick_params(axis="x", rotation=20)
axes[1].grid(axis="y", alpha=0.3)
axes[1].spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "usage-trend.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "usage-trend.png")))
plt.close(fig)
print("趋势最低组流失率:", round(float(trend_stats.iloc[0]), 1), "%")
print("趋势最高组流失率:", round(float(trend_stats.iloc[-1]), 1), "%")


from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

base_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
time_cols = ["signup_month", "signup_weekday", "is_weekend", "tenure_days"]
window_cols = ["usage_mean_6m", "usage_std_6m", "usage_max_6m", "usage_trend", "active_months"]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)


def evaluate(name, cols):
    pipeline = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])
    scores = cross_val_score(pipeline, data[cols], data["churned"], cv=cv, scoring="roc_auc")
    return {"特征组": name, "字段数": len(cols), "AUC 均值": round(scores.mean(), 4)}


rows = [
    evaluate("基础数值", base_cols),
    evaluate("基础 + 时间", base_cols + time_cols),
    evaluate("基础 + 窗口", base_cols + window_cols),
    evaluate("全部", base_cols + time_cols + window_cols),
]
display(pd.DataFrame(rows))
