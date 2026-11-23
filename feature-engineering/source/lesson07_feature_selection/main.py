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

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

df = pd.read_csv(data_path("customer_churn.csv"), parse_dates=["signup_date"])
df["support_notes"] = df["support_notes"].fillna("")

numeric_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
cat_cols = ["region", "city", "plan", "contract_type", "payment_method", "auto_renew"]
feature_cols = numeric_cols + cat_cols

train, test = train_test_split(
    df, test_size=0.25, stratify=df["churned"], random_state=SEED
)

pre = ColumnTransformer([
    ("num", Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
])
pre.fit(train[feature_cols], train["churned"])
X_train = pre.transform(train[feature_cols])
y_train = train["churned"].to_numpy()
feature_names = pre.get_feature_names_out()

print("原始字段数:", len(feature_cols))
print("编码后维度:", X_train.shape[1])
print("前 12 个特征名:", ", ".join(feature_names[:12]))


from functools import partial

from sklearn.feature_selection import mutual_info_classif

mi_scores = mutual_info_classif(X_train, y_train, random_state=SEED)
ranking = pd.DataFrame({
    "feature": feature_names,
    "mutual_info": mi_scores,
}).sort_values("mutual_info", ascending=False)

display(ranking.head(15).round(4))
print("互信息为 0 的特征数:", int((mi_scores == 0).sum()))


from sklearn.base import clone
from sklearn.feature_selection import RFE, SelectFromModel, SelectKBest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
scoring_func = partial(mutual_info_classif, random_state=SEED)


def evaluate(name, selector):
    steps = [("pre", clone(pre))]
    if selector is not None:
        steps.append(("select", selector))
    steps.append(("model", LogisticRegression(max_iter=1000, random_state=SEED)))
    pipeline = Pipeline(steps)
    scores = cross_val_score(
        pipeline, train[feature_cols], train["churned"], cv=cv, scoring="roc_auc"
    )
    if selector is None:
        n_features = X_train.shape[1]
    else:
        n_features = int(selector.fit(X_train, y_train).get_support().sum())
    return {
        "选择方法": name,
        "保留特征数": n_features,
        "AUC 均值": round(scores.mean(), 4),
        "AUC 标准差": round(scores.std(), 4),
    }


rows = [
    evaluate("全部特征", None),
    evaluate("过滤式：互信息 Top 20", SelectKBest(scoring_func, k=20)),
    evaluate("包裹式：RFE 20 个", RFE(
        LogisticRegression(max_iter=1000, random_state=SEED),
        n_features_to_select=20,
        step=10,
    )),
    evaluate("嵌入式：L1 正则", SelectFromModel(
        LogisticRegression(
            l1_ratio=1.0, solver="liblinear", C=0.3, max_iter=2000, random_state=SEED
        ),
        threshold="mean",
        max_features=30,
    )),
]
display(pd.DataFrame(rows))


ks = [5, 10, 20, 30, 40, 60, 80]
aucs = []
for k in ks:
    pipeline = Pipeline([
        ("pre", clone(pre)),
        ("select", SelectKBest(scoring_func, k=min(k, X_train.shape[1]))),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])
    scores = cross_val_score(
        pipeline, train[feature_cols], train["churned"], cv=cv, scoring="roc_auc"
    )
    aucs.append(scores.mean())

fig, ax = plt.subplots(figsize=(7.2, 4))
ax.plot(ks, aucs, marker="o", color="#4C78A8", linewidth=2)
best_index = int(np.argmax(aucs))
ax.scatter([ks[best_index]], [aucs[best_index]], color="#C44E52", zorder=3)
ax.annotate(f"k={ks[best_index]}, AUC={aucs[best_index]:.3f}",
            xy=(ks[best_index], aucs[best_index]),
            xytext=(10, -18), textcoords="offset points")
ax.set_xlabel("保留特征数 k")
ax.set_ylabel("交叉验证 ROC AUC")
ax.set_title("过滤式选择的特征数量与效果")
ax.grid(alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "select-k.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "select-k.png")))
plt.close(fig)
print("最佳 k:", ks[best_index], "AUC:", round(aucs[best_index], 4))
print("全部特征 AUC:", round(aucs[-1], 4))
