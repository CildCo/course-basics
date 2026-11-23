import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


df = pd.read_csv(data_path("customers.csv"))
print("样本数:", len(df), "流失率:", round(float(df["churn"].mean()), 3))
print("城市数:", df["city"].nunique(), "套餐数:", df["plan"].nunique())
df.head()


numeric = ["age", "income", "tenure_months"]
categorical = ["city", "plan"]
train_df, test_df = train_test_split(
    df, test_size=0.25, stratify=df["churn"], random_state=RANDOM_STATE
)
train_df = train_df.reset_index(drop=True)
test_df = test_df.reset_index(drop=True)

onehot_model = Pipeline([
    ("prep", ColumnTransformer([
        ("num", StandardScaler(), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])),
    ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
])

onehot_cv = cross_val_score(
    onehot_model, train_df[numeric + categorical], train_df["churn"],
    cv=5, scoring="roc_auc",
).mean()
onehot_model.fit(train_df[numeric + categorical], train_df["churn"])
onehot_test = roc_auc_score(
    test_df["churn"],
    onehot_model.predict_proba(test_df[numeric + categorical])[:, 1],
)
print("独热编码 交叉验证 AUC:", round(float(onehot_cv), 4))
print("独热编码 测试集 AUC:", round(float(onehot_test), 4))


def target_encode(train, apply, column, prior, smoothing=20):
    stats = train.groupby(column)["churn"].agg(["mean", "count"])
    encoded = (stats["mean"] * stats["count"] + prior * smoothing) / (stats["count"] + smoothing)
    return apply[column].map(encoded).fillna(prior)


def with_encoding(train, apply, prior):
    out = apply[numeric].copy()
    out["city"] = target_encode(train, apply, "city", prior)
    out["plan"] = target_encode(train, apply, "plan", prior)
    return out


prior = train_df["churn"].mean()
train_full = with_encoding(train_df, train_df, prior)
test_full = with_encoding(train_df, test_df, prior)

full_model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
naive_cv = cross_val_score(
    full_model, train_full, train_df["churn"], cv=5, scoring="roc_auc"
).mean()
full_model.fit(train_full, train_df["churn"])
target_test = roc_auc_score(
    test_df["churn"], full_model.predict_proba(test_full)[:, 1]
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
fold_scores = []
for tr_index, va_index in skf.split(train_df, train_df["churn"]):
    part = train_df.iloc[tr_index]
    hold = train_df.iloc[va_index]
    fold_prior = part["churn"].mean()
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    model.fit(with_encoding(part, part, fold_prior), part["churn"])
    prob = model.predict_proba(with_encoding(part, hold, fold_prior))[:, 1]
    fold_scores.append(roc_auc_score(hold["churn"], prob))
fold_safe_cv = float(np.mean(fold_scores))

print("全量标签编码 交叉验证 AUC:", round(float(naive_cv), 4))
print("折内编码 交叉验证 AUC:", round(fold_safe_cv, 4))
print("目标编码 测试集 AUC:", round(float(target_test), 4))


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

labels = ["独热编码\n（交叉验证）", "目标编码\n全量标签", "目标编码\n折内标签", "目标编码\n测试集"]
values = [onehot_cv, naive_cv, fold_safe_cv, target_test]
colors = ["#9DB2C7", "#C97B63", "#5B7DB1", "#7FA88B"]

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(labels, values, color=colors, width=0.6)
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.004,
            f"{value:.3f}", ha="center", fontsize=10)
ax.set_ylim(min(values) - 0.05, max(values) + 0.03)
ax.set_ylabel("AUC")
ax.set_title("同一种编码，不同评估口径")
ax.grid(axis="y", alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "target-encoding.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "target-encoding.png")))
plt.close(fig)


city_stats = (
    train_df.groupby("city")
    .agg(样本数=("churn", "size"), 流失率=("churn", "mean"))
    .sort_values("样本数")
)
city_stats.head(8).round(3)


def encode_ids(fit_ids, fit_y, apply_ids, prior, smoothing=5):
    stats = pd.DataFrame({
        "customer_id": fit_ids.values,
        "churn": fit_y.values,
    }).groupby("customer_id")["churn"].agg(["mean", "count"])
    encoded = (stats["mean"] * stats["count"] + prior * smoothing) / (stats["count"] + smoothing)
    return apply_ids.map(encoded).fillna(prior).to_numpy().reshape(-1, 1)


id_prior = train_df["churn"].mean()
id_train = encode_ids(train_df["customer_id"], train_df["churn"], train_df["customer_id"], id_prior)
id_test = encode_ids(train_df["customer_id"], train_df["churn"], test_df["customer_id"], id_prior)

id_model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
id_cv = cross_val_score(id_model, id_train, train_df["churn"], cv=5, scoring="roc_auc").mean()
id_model.fit(id_train, train_df["churn"])
id_test_auc = roc_auc_score(test_df["churn"], id_model.predict_proba(id_test)[:, 1])

id_skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
id_fold_scores = []
for tr_index, va_index in id_skf.split(train_df, train_df["churn"]):
    part = train_df.iloc[tr_index]
    hold = train_df.iloc[va_index]
    part_prior = part["churn"].mean()
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    model.fit(
        encode_ids(part["customer_id"], part["churn"], part["customer_id"], part_prior),
        part["churn"],
    )
    prob = model.predict_proba(
        encode_ids(part["customer_id"], part["churn"], hold["customer_id"], part_prior)
    )[:, 1]
    id_fold_scores.append(roc_auc_score(hold["churn"], prob))

print("客户编号 全量编码 交叉验证 AUC:", round(float(id_cv), 3))
print("客户编号 折内编码 交叉验证 AUC:", round(float(np.mean(id_fold_scores)), 3))
print("客户编号 测试集 AUC:", round(float(id_test_auc), 3))
