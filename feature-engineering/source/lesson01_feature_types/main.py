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
print("客户数:", len(df), "字段数:", df.shape[1])
print("流失率:", f"{df['churned'].mean():.1%}")
display(df.head(3))


type_table = pd.DataFrame({
    "字段": df.columns,
    "类型": [str(t) for t in df.dtypes],
    "唯一值": [df[c].nunique() for c in df.columns],
    "缺失数": [int(df[c].isna().sum()) for c in df.columns],
})
display(type_table)
print("数值特征:", ", ".join(df.drop(columns=["churned"]).select_dtypes("number").columns))
print("文本特征: support_notes")
print("时间特征: signup_date")


from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

numeric_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
categorical_cols = ["region", "plan", "contract_type", "payment_method", "auto_renew"]


def make_pipeline(extra_categorical=()):
    numeric = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    pre = ColumnTransformer([
        ("num", numeric, numeric_cols),
        ("cat", categorical, categorical_cols + list(extra_categorical)),
    ])
    return Pipeline([
        ("pre", pre),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])


data = df.sort_values("signup_date").reset_index(drop=True)
cut = int(len(data) * 0.8)
train, test = data.iloc[:cut], data.iloc[cut:]

scores = {}
for name, extra in [("干净特征", ()), ("混入 churn_reason", ("churn_reason",))]:
    pipeline = make_pipeline(extra)
    pipeline.fit(train, train["churned"])
    scores[name] = roc_auc_score(test["churned"], pipeline.predict_proba(test)[:, 1])
    print(f"{name}: 测试 AUC = {scores[name]:.3f}")
print("训练集客户数:", len(train), "测试集客户数:", len(test))


labels = list(scores)
values = [scores[name] for name in labels]
colors = ["#4C78A8", "#C44E52"]

fig, ax = plt.subplots(figsize=(6.8, 4))
bars = ax.bar(labels, values, color=colors, width=0.5)
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.015, f"{value:.3f}",
            ha="center", va="bottom", fontsize=10)
ax.set_ylim(0, 1.08)
ax.set_ylabel("测试集 ROC AUC")
ax.set_title("目标泄漏会把线下指标推到失真")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "leakage-auc.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "leakage-auc.png")))
plt.close(fig)
print("干净特征与泄漏特征的差距:", round(values[1] - values[0], 3))
