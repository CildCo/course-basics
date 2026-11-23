import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import time

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
import lightgbm as lgb

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(1 - data.target, name="malignant")

X_tmp, X_test, y_tmp, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
X_train, X_valid, y_train, y_valid = train_test_split(
    X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=RANDOM_STATE
)
print("训练:", X_train.shape, "验证:", X_valid.shape, "测试:", X_test.shape)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

booster = lgb.LGBMClassifier(
    n_estimators=300,
    learning_rate=0.05,
    num_leaves=15,
    min_child_samples=20,
    subsample=0.9,
    colsample_bytree=0.8,
    random_state=RANDOM_STATE,
    n_jobs=1,
    force_col_wise=True,
    verbose=-1,
)

start = time.perf_counter()
booster.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_valid, y_valid)],
    eval_names=["训练集", "验证集"],
    eval_metric="binary_logloss",
    callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(0)],
)
fit_seconds = time.perf_counter() - start

history = booster.evals_result_
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(history["训练集"]["binary_logloss"], color="#5B7DB1", label="训练集")
ax.plot(history["验证集"]["binary_logloss"], color="#C97B63", label="验证集")
ax.axvline(booster.best_iteration_ - 1, linestyle="--", color="#888888", label="早停位置")
ax.set_xlabel("提升轮数")
ax.set_ylabel("对数损失")
ax.set_title("训练损失与验证损失")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "lgb-curve.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "lgb-curve.png")))
plt.close(fig)

print("最佳轮数:", booster.best_iteration_)
print("训练耗时:", round(fit_seconds, 2), "秒")
print("测试 AUC:", round(roc_auc_score(y_test, booster.predict_proba(X_test)[:, 1]), 4))


rf = RandomForestClassifier(
    n_estimators=300, min_samples_leaf=2,
    random_state=RANDOM_STATE, n_jobs=1,
)
start = time.perf_counter()
rf.fit(X_train, y_train)
rf_seconds = time.perf_counter() - start

rows = []
for name, model, seconds in [
    ("随机森林", rf, rf_seconds),
    ("LightGBM", booster, fit_seconds),
]:
    prob = model.predict_proba(X_test)[:, 1]
    rows.append({
        "模型": name,
        "训练耗时（秒）": seconds,
        "测试准确率": accuracy_score(y_test, prob >= 0.5),
        "测试 AUC": roc_auc_score(y_test, prob),
        "测试 LogLoss": log_loss(y_test, prob),
    })

pd.DataFrame(rows).round(3)
