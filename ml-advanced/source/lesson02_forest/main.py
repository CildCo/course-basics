import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    RepeatedStratifiedKFold, cross_validate, cross_val_score, train_test_split,
)
from sklearn.tree import DecisionTreeClassifier

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

X_array, y_array = make_classification(
    n_samples=800,
    n_features=20,
    n_informative=6,
    n_redundant=4,
    flip_y=0.12,
    class_sep=0.8,
    random_state=RANDOM_STATE,
)
X = pd.DataFrame(X_array, columns=[f"feature_{i:02d}" for i in range(1, 21)])
y = pd.Series(y_array, name="fault")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)
print("训练集:", X_train.shape, "测试集:", X_test.shape)
print("故障比例:", round(float(y.mean()), 3))


rows = []
for depth in [1, 3, 5, None]:
    tree = DecisionTreeClassifier(max_depth=depth, random_state=RANDOM_STATE)
    scores = cross_validate(
        tree, X_train, y_train,
        cv=5, scoring="accuracy", return_train_score=True,
    )
    rows.append({
        "最大深度": "不限" if depth is None else depth,
        "训练准确率": scores["train_score"].mean(),
        "验证准确率": scores["test_score"].mean(),
        "验证波动": scores["test_score"].std(),
    })

pd.DataFrame(rows).round(3)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

forest = RandomForestClassifier(
    n_estimators=30, warm_start=True, oob_score=True,
    random_state=RANDOM_STATE, n_jobs=1,
)
records = []
for trees in range(30, 161, 10):
    forest.set_params(n_estimators=trees)
    forest.fit(X_train, y_train)
    records.append({
        "trees": trees,
        "oob_error": 1 - forest.oob_score_,
        "test_error": 1 - forest.score(X_test, y_test),
    })

curve = pd.DataFrame(records)
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(curve["trees"], curve["oob_error"], marker="o", color="#5B7DB1", label="袋外误差")
ax.plot(curve["trees"], curve["test_error"], marker="s", color="#C97B63", label="测试集误差")
ax.set_xlabel("树的数量")
ax.set_ylabel("错误率")
ax.set_title("袋外误差随树数量的变化")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "oob-error.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "oob-error.png")))
plt.close(fig)

print("袋外误差:", round(float(curve["oob_error"].iloc[-1]), 3))
print("测试误差:", round(float(curve["test_error"].iloc[-1]), 3))


cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=RANDOM_STATE)

rows = []
for name, model in [
    ("单棵决策树（不限深度）", DecisionTreeClassifier(random_state=RANDOM_STATE)),
    ("随机森林（150 棵）", RandomForestClassifier(
        n_estimators=150, random_state=RANDOM_STATE, n_jobs=1,
    )),
]:
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy")
    rows.append({
        "模型": name,
        "验证准确率": scores.mean(),
        "验证波动": scores.std(),
    })

pd.DataFrame(rows).round(3)
