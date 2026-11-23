import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import time

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import (
    GridSearchCV, RandomizedSearchCV, train_test_split,
)
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
print("训练集:", X_train.shape, "测试集:", X_test.shape)


def make_model():
    return Pipeline([
        ("scale", StandardScaler()),
        ("clf", RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=1)),
    ])


param_grid = {
    "clf__max_depth": [3, 5, None],
    "clf__min_samples_leaf": [1, 3],
    "clf__n_estimators": [80, 120],
}

grid = GridSearchCV(
    make_model(), param_grid,
    cv=3, scoring="roc_auc", return_train_score=True, n_jobs=1,
)
start = time.perf_counter()
grid.fit(X_train, y_train)
grid_seconds = time.perf_counter() - start

print("组合数:", len(grid.cv_results_["params"]))
print("最佳参数:", grid.best_params_)
print("最佳交叉验证 AUC:", round(float(grid.best_score_), 4))
print("总耗时:", round(grid_seconds, 2), "秒")

grid_table = pd.DataFrame({
    "max_depth": [p["clf__max_depth"] for p in grid.cv_results_["params"]],
    "min_samples_leaf": [p["clf__min_samples_leaf"] for p in grid.cv_results_["params"]],
    "n_estimators": [p["clf__n_estimators"] for p in grid.cv_results_["params"]],
    "训练 AUC": grid.cv_results_["mean_train_score"],
    "验证 AUC": grid.cv_results_["mean_test_score"],
    "耗时（秒）": grid.cv_results_["mean_fit_time"],
}).sort_values("验证 AUC", ascending=False)
grid_table["max_depth"] = grid_table["max_depth"].map(
    lambda value: "不限" if pd.isna(value) else int(value)
)
grid_table.head(6).round(4)


param_distributions = {
    "clf__max_depth": [3, 4, 5, 6, 8, None],
    "clf__min_samples_leaf": [1, 2, 3, 5, 8],
    "clf__n_estimators": [60, 80, 100, 120, 160],
    "clf__max_features": ["sqrt", "log2", None],
}

random_search = RandomizedSearchCV(
    make_model(), param_distributions,
    n_iter=10, cv=3, scoring="roc_auc",
    random_state=RANDOM_STATE, n_jobs=1,
)
start = time.perf_counter()
random_search.fit(X_train, y_train)
random_seconds = time.perf_counter() - start

experiment_log = pd.DataFrame([
    {
        "实验": "GridSearchCV",
        "组合数": len(grid.cv_results_["params"]),
        "耗时（秒）": round(grid_seconds, 2),
        "最佳交叉验证 AUC": round(float(grid.best_score_), 4),
        "最佳参数": str(grid.best_params_),
    },
    {
        "实验": "RandomizedSearchCV",
        "组合数": len(random_search.cv_results_["params"]),
        "耗时（秒）": round(random_seconds, 2),
        "最佳交叉验证 AUC": round(float(random_search.best_score_), 4),
        "最佳参数": str(random_search.best_params_),
    },
])
experiment_log.to_csv(OUTPUT / "search-log.csv", index=False, encoding="utf-8")
print("最佳随机搜索参数:", random_search.best_params_)
experiment_log


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(
    grid.cv_results_["mean_fit_time"], grid.cv_results_["mean_test_score"],
    color="#5B7DB1", label="网格搜索", s=50,
)
ax.scatter(
    random_search.cv_results_["mean_fit_time"], random_search.cv_results_["mean_test_score"],
    color="#C97B63", label="随机搜索", s=50, marker="s",
)
ax.set_xlabel("单次拟合平均耗时（秒）")
ax.set_ylabel("验证 AUC")
ax.set_title("搜索预算与验证分数")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "search-budget.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "search-budget.png")))
plt.close(fig)


best_model = grid.best_estimator_
test_prob = best_model.predict_proba(X_test)[:, 1]
print("最终测试 AUC:", round(float(roc_auc_score(y_test, test_prob)), 4))
print("实验记录已写入:", OUTPUT / "search-log.csv")
