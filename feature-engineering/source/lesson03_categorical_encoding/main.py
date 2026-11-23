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
df["support_notes"] = df["support_notes"].fillna("")

plan_stats = df.groupby("plan").agg(
    customers=("customer_id", "count"),
    churn_rate=("churned", "mean"),
).sort_values("churn_rate", ascending=False)
plan_stats["churn_rate"] = (plan_stats["churn_rate"] * 100).round(1)
display(plan_stats)

print("城市数:", df["city"].nunique())
print("最大类别客户数:", df["city"].value_counts().max())
print("最小类别客户数:", df["city"].value_counts().min())


city_stats = df.groupby("city").agg(
    customers=("customer_id", "count"),
    churn_rate=("churned", "mean"),
).sort_values("churn_rate")

fig, ax = plt.subplots(figsize=(8.2, 6))
ax.barh(city_stats.index, city_stats["churn_rate"] * 100, color="#6B8E9F")
ax.axvline(df["churned"].mean() * 100, color="#C44E52", linestyle="--", label="整体流失率")
ax.set_xlabel("流失率（%）")
ax.set_title("各城市流失率（按升序）")
ax.legend(frameon=False)
ax.grid(axis="x", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "city-churn.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "city-churn.png")))
plt.close(fig)
print("流失率最高城市:", city_stats.index[-1], f"{city_stats['churn_rate'].iloc[-1]:.1%}")
print("流失率最低城市:", city_stats.index[0], f"{city_stats['churn_rate'].iloc[0]:.1%}")


from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

numeric_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
cat_cols = ["region", "city", "plan", "contract_type", "payment_method", "auto_renew"]
X = df[numeric_cols + cat_cols]
y = df["churned"]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)


def numeric_pre():
    return Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])


def evaluate(name, pre):
    pipeline = Pipeline([
        ("pre", pre),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    return {"编码": name, "AUC 均值": round(scores.mean(), 4), "AUC 标准差": round(scores.std(), 4)}


onehot_pre = ColumnTransformer([
    ("num", numeric_pre(), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
])
rows = [evaluate("OneHot", onehot_pre)]
print("OneHot 编码后类别列数:", onehot_pre.fit_transform(X).shape[1] - len(numeric_cols))
display(pd.DataFrame(rows))


from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, cols):
        self.cols = cols

    def fit(self, X, y=None):
        self.maps_ = {col: X[col].value_counts(normalize=True) for col in self.cols}
        return self

    def transform(self, X):
        columns = [X[col].map(self.maps_[col]).fillna(0.0).to_numpy() for col in self.cols]
        return np.column_stack(columns)


class OutOfFoldTargetEncoder(BaseEstimator, TransformerMixin):
    # 训练时折外编码，预测时使用全训练集映射
    def __init__(self, col, smoothing=10, n_splits=5, random_state=42):
        self.col = col
        self.smoothing = smoothing
        self.n_splits = n_splits
        self.random_state = random_state

    def _mapping(self, X, y):
        frame = pd.DataFrame({"cat": X[self.col].to_numpy(), "target": np.asarray(y)})
        stats = frame.groupby("cat")["target"].agg(["mean", "count"])
        prior = float(np.mean(y))
        mapping = (stats["mean"] * stats["count"] + prior * self.smoothing) / (
            stats["count"] + self.smoothing
        )
        return mapping, prior

    def fit(self, X, y):
        self.mapping_, self.prior_ = self._mapping(X, y)
        return self

    def transform(self, X):
        values = X[self.col].map(self.mapping_).fillna(self.prior_).astype(float)
        return values.to_numpy().reshape(-1, 1)

    def fit_transform(self, X, y=None, **fit_params):
        if y is None:
            raise ValueError("Target 编码需要标签")
        X = pd.DataFrame(X)
        y = pd.Series(np.asarray(y), index=X.index)
        oof = pd.Series(np.nan, index=X.index, dtype=float)
        splitter = StratifiedKFold(
            n_splits=self.n_splits, shuffle=True, random_state=self.random_state
        )
        for train_idx, valid_idx in splitter.split(X, y):
            mapping, prior = self._mapping(X.iloc[train_idx], y.iloc[train_idx])
            oof.iloc[valid_idx] = X.iloc[valid_idx][self.col].map(mapping).fillna(prior).to_numpy()
        self.fit(X, y)
        return oof.to_numpy().reshape(-1, 1)


freq_pre = ColumnTransformer([
    ("num", numeric_pre(), numeric_cols),
    ("cat", FrequencyEncoder(cat_cols), cat_cols),
])

other_cats = [col for col in cat_cols if col != "city"]
target_pre = ColumnTransformer([
    ("num", numeric_pre(), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), other_cats),
    ("city", OutOfFoldTargetEncoder("city", smoothing=10), ["city"]),
])

rows = [
    evaluate("OneHot", onehot_pre),
    evaluate("频率编码", freq_pre),
    evaluate("Target 编码（城市）", target_pre),
]
display(pd.DataFrame(rows))
print("频率编码维度:", freq_pre.fit_transform(X).shape[1] - len(numeric_cols))
print("Target 编码维度:", target_pre.fit_transform(X, y).shape[1] - len(numeric_cols))
