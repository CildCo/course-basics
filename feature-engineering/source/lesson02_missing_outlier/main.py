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
print("客户数:", len(df))
print("整体流失率:", f"{df['churned'].mean():.1%}")

missing = pd.DataFrame({
    "missing": df.isna().sum(),
    "ratio": df.isna().mean(),
})
missing = missing[missing["missing"] > 0].sort_values("ratio", ascending=False)
missing["ratio"] = missing["ratio"].map(lambda v: f"{v:.1%}")
display(missing)


for col in ["age", "monthly_fee", "monthly_usage_gb"]:
    flag = df[col].isna()
    print(
        f"{col}: 缺失 {int(flag.sum())} 行，"
        f"缺失组流失率 {df.loc[flag, 'churned'].mean():.1%}，"
        f"完整组 {df.loc[~flag, 'churned'].mean():.1%}"
    )


fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, col in zip(axes, ["monthly_fee", "monthly_usage_gb"]):
    values = df[col].dropna()
    upper = values.quantile(0.99)
    ax.hist(np.clip(values, 0, upper), bins=40, color="#7A9CC6", edgecolor="white")
    ax.axvline(values.mean(), color="#C44E52", linestyle="--", label=f"均值 {values.mean():.1f}")
    ax.axvline(values.median(), color="#55A868", linestyle="--", label=f"中位数 {values.median():.1f}")
    ax.set_title(col)
    ax.set_xlabel("取值")
    ax.set_ylabel("客户数")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "missing-outlier.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "missing-outlier.png")))
plt.close(fig)
print("monthly_fee 均值/中位数:", round(df["monthly_fee"].mean(), 2), round(df["monthly_fee"].median(), 2))
print("monthly_usage_gb 均值/中位数:", round(df["monthly_usage_gb"].mean(), 2), round(df["monthly_usage_gb"].median(), 2))


from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

numeric_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
X = df[numeric_cols]
y = df["churned"]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

rows = []
strategies = [
    ("均值填充", SimpleImputer(strategy="mean")),
    ("中位数填充", SimpleImputer(strategy="median")),
    ("中位数+缺失指示", SimpleImputer(strategy="median", add_indicator=True)),
]
for name, imputer in strategies:
    pipeline = Pipeline([
        ("imp", imputer),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    rows.append({
        "填充方式": name,
        "AUC 均值": round(scores.mean(), 4),
        "AUC 标准差": round(scores.std(), 4),
    })
display(pd.DataFrame(rows))


from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import RobustScaler


class IQRClipper(BaseEstimator, TransformerMixin):
    # 只在 fit 阶段学习上下界，transform 阶段只做截断
    def __init__(self, factor=1.5):
        self.factor = factor

    def fit(self, X, y=None):
        frame = pd.DataFrame(X)
        q1 = frame.quantile(0.25)
        q3 = frame.quantile(0.75)
        iqr = q3 - q1
        self.lower_ = q1 - self.factor * iqr
        self.upper_ = q3 + self.factor * iqr
        return self

    def transform(self, X):
        frame = pd.DataFrame(X)
        return frame.clip(self.lower_, self.upper_, axis=1).to_numpy()


pipelines = {
    "原始值 + StandardScaler": Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ]),
    "IQR 截断 + StandardScaler": Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("clip", IQRClipper()),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ]),
    "原始值 + RobustScaler": Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", RobustScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ]),
}

rows = []
for name, pipeline in pipelines.items():
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    rows.append({
        "异常值处理": name,
        "AUC 均值": round(scores.mean(), 4),
        "AUC 标准差": round(scores.std(), 4),
    })
display(pd.DataFrame(rows))

fee = df["monthly_fee"].dropna()
q1, q3 = fee.quantile([0.25, 0.75])
iqr = q3 - q1
print("monthly_fee 上界:", round(q3 + 1.5 * iqr, 1), "超过上界的客户数:", int((fee > q3 + 1.5 * iqr).sum()))
print("monthly_usage_gb 最大值:", round(df["monthly_usage_gb"].max(), 1))
