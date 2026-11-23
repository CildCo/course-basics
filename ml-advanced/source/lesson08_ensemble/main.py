import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier, StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(1 - data.target, name="malignant")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)
print("训练集:", X_train.shape)


def scaled(model):
    return Pipeline([("scale", StandardScaler()), ("model", model)])


base_models = {
    "逻辑回归": scaled(LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
    "随机森林": RandomForestClassifier(
        n_estimators=100, max_depth=6,
        random_state=RANDOM_STATE, n_jobs=1,
    ),
    "K 近邻": scaled(KNeighborsClassifier(n_neighbors=15)),
}

voting = VotingClassifier(
    estimators=[(name, model) for name, model in base_models.items()],
    voting="soft",
)
stacking = StackingClassifier(
    estimators=[(name, model) for name, model in base_models.items()],
    final_estimator=LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
    cv=5,
    stack_method="predict_proba",
    n_jobs=1,
)

rows = []
for name, model in [
    *base_models.items(),
    ("软投票", voting),
    ("堆叠", stacking),
]:
    scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")
    rows.append({
        "模型": name,
        "交叉验证 AUC": scores.mean(),
        "波动": scores.std(),
    })

pd.DataFrame(rows).round(4)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

table = pd.DataFrame(rows)
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(
    table["模型"], table["交叉验证 AUC"],
    yerr=table["波动"], capsize=4,
    color=["#9DB2C7", "#7FA88B", "#B9A44C", "#5B7DB1", "#C97B63"],
    width=0.6,
)
ax.set_ylim(table["交叉验证 AUC"].min() - 0.02, table["交叉验证 AUC"].max() + 0.01)
ax.set_ylabel("交叉验证 AUC")
ax.set_title("单模型与集成模型的收益对比")
ax.grid(axis="y", alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "ensemble-gain.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "ensemble-gain.png")))
plt.close(fig)


prediction_frame = {}
for name, model in base_models.items():
    prediction_frame[name] = cross_val_predict(
        model, X_train, y_train, cv=5, method="predict_proba"
    )[:, 1]

corr = pd.DataFrame(prediction_frame).corr()
corr.round(3)
