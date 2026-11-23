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

df = pd.read_csv(data_path("customer_churn.csv"), parse_dates=["signup_date"])
cols = ["monthly_fee", "monthly_usage_gb", "support_calls", "last_login_days_ago"]
rows = []
for col in cols:
    values = df[col].dropna()
    rows.append({
        "字段": col,
        "偏度": round(values.skew(), 2),
        "均值": round(values.mean(), 1),
        "中位数": round(values.median(), 1),
        "最大值": round(values.max(), 1),
    })
display(pd.DataFrame(rows))


raw = df["monthly_usage_gb"].dropna()
logged = np.log1p(raw)

fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
axes[0].hist(np.clip(raw, 0, raw.quantile(0.99)), bins=40, color="#C9A66B", edgecolor="white")
axes[0].set_title("原始用量")
axes[1].hist(logged, bins=40, color="#6B9E8A", edgecolor="white")
axes[1].set_title("log1p 之后")
for ax in axes:
    ax.set_xlabel("取值")
    ax.set_ylabel("客户数")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "log-transform.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "log-transform.png")))
plt.close(fig)
print("原始偏度:", round(raw.skew(), 2))
print("log1p 后偏度:", round(logged.skew(), 2))
print("原始最大值:", round(raw.max(), 1), "log1p 后最大值:", round(logged.max(), 2))


from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    MinMaxScaler,
    RobustScaler,
    StandardScaler,
)
from sklearn.impute import SimpleImputer

numeric_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
X = df[numeric_cols]
y = df["churned"]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

variants = [
    ("原始值", None),
    ("StandardScaler", StandardScaler()),
    ("RobustScaler", RobustScaler()),
    ("log1p + StandardScaler", Pipeline([
        ("log", FunctionTransformer(np.log1p)),
        ("scale", StandardScaler()),
    ])),
    ("MinMaxScaler", MinMaxScaler()),
]

rows = []
for name, transform in variants:
    steps = [("imp", SimpleImputer(strategy="median"))]
    if transform is not None:
        steps.append(("transform", transform))
    steps.append(("model", LogisticRegression(max_iter=1000, random_state=SEED)))
    scores = cross_val_score(Pipeline(steps), X, y, cv=cv, scoring="roc_auc")
    rows.append({
        "缩放方式": name,
        "AUC 均值": round(scores.mean(), 4),
        "AUC 标准差": round(scores.std(), 4),
    })
display(pd.DataFrame(rows))


fee_bins = pd.qcut(df["monthly_fee"], q=4, duplicates="drop")
bin_stats = df.assign(fee_bin=fee_bins).groupby("fee_bin", observed=True).agg(
    customers=("customer_id", "count"),
    churn_rate=("churned", "mean"),
)
bin_stats["churn_rate"] = (bin_stats["churn_rate"] * 100).round(1)
display(bin_stats)

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import KBinsDiscretizer

bin_cols = ["monthly_fee", "monthly_usage_gb"]
other_cols = [col for col in numeric_cols if col not in bin_cols]
bin_pre = ColumnTransformer([
    ("bin", Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("bin", KBinsDiscretizer(n_bins=8, encode="ordinal", strategy="quantile")),
    ]), bin_cols),
    ("num", Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]), other_cols),
])
bin_pipeline = Pipeline([
    ("pre", bin_pre),
    ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
])
raw_pipeline = Pipeline([
    ("imp", SimpleImputer(strategy="median")),
    ("scale", StandardScaler()),
    ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
])
for name, pipeline in [("连续值", raw_pipeline), ("月费与用量分 8 箱", bin_pipeline)]:
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    print(f"{name}: AUC {scores.mean():.4f} ± {scores.std():.4f}")
