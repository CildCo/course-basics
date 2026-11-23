import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    precision_recall_curve, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

X, y = make_classification(
    n_samples=8000,
    n_features=15,
    n_informative=10,
    n_redundant=3,
    weights=[0.98, 0.02],
    flip_y=0.02,
    class_sep=1.8,
    random_state=RANDOM_STATE,
)
X_tmp, X_test, y_tmp, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
X_train, X_valid, y_train, y_valid = train_test_split(
    X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=RANDOM_STATE
)
print("训练:", X_train.shape, "验证:", X_valid.shape, "测试:", X_test.shape)
print("训练集正例比例:", round(float(y_train.mean()), 4))


def predict_scores(y_true, prob, threshold=0.5):
    pred = (prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
    return {
        "准确率": accuracy_score(y_true, pred),
        "精确率": precision_score(y_true, pred, zero_division=0),
        "召回率": recall_score(y_true, pred, zero_division=0),
        "F1": f1_score(y_true, pred, zero_division=0),
        "PR AUC": average_precision_score(y_true, prob),
        "漏报": int(fn),
        "误报": int(fp),
    }


def scaled_logistic(**kwargs):
    return Pipeline([
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(max_iter=3000, random_state=RANDOM_STATE, **kwargs)),
    ])


plain = scaled_logistic()
plain.fit(X_train, y_train)
prob_plain = plain.predict_proba(X_valid)[:, 1]

balanced = scaled_logistic(class_weight="balanced")
balanced.fit(X_train, y_train)
prob_balanced = balanced.predict_proba(X_valid)[:, 1]

rng = np.random.RandomState(RANDOM_STATE)
positive = np.flatnonzero(y_train == 1)
negative = np.flatnonzero(y_train == 0)
extra = rng.choice(positive, size=len(negative) - len(positive), replace=True)
X_over = np.vstack([X_train, X_train[extra]])
y_over = np.concatenate([y_train, y_train[extra]])

over = scaled_logistic()
over.fit(X_over, y_over)
prob_over = over.predict_proba(X_valid)[:, 1]

rows = []
for name, prob in [
    ("普通逻辑回归 @0.50", prob_plain),
    ("class_weight @0.50", prob_balanced),
    ("随机过采样 @0.50", prob_over),
]:
    row = {"做法": name}
    row.update(predict_scores(y_valid, prob, 0.5))
    rows.append(row)

pd.DataFrame(rows).round(3)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

precision, recall, thresholds = precision_recall_curve(y_valid, prob_balanced)
f1_values = 2 * precision * recall / (precision + recall + 1e-12)
best_index = int(np.argmax(f1_values[:-1]))
best_threshold = float(thresholds[best_index])

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(recall, precision, color="#5B7DB1", label="class_weight 模型")
ax.scatter(recall[best_index], precision[best_index], color="#C97B63", zorder=3,
           label=f"阈值 {best_threshold:.2f}")
ax.axhline(y_valid.mean(), linestyle="--", color="#888888", label="正例比例")
ax.set_xlabel("召回率")
ax.set_ylabel("精确率")
ax.set_title("验证集上的 PR 曲线")
ax.legend(frameon=False)
ax.grid(alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "imbalance-pr.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "imbalance-pr.png")))
plt.close(fig)

print("验证集最优阈值:", round(best_threshold, 3))
print("对应 F1:", round(float(f1_values[best_index]), 3))


prob_test = balanced.predict_proba(X_test)[:, 1]
rows = []
for name, threshold in [("class_weight @0.50", 0.5), (f"class_weight @{best_threshold:.2f}", best_threshold)]:
    row = {"测试口径": name}
    row.update(predict_scores(y_test, prob_test, threshold))
    rows.append(row)

table = pd.DataFrame(rows).round(3)
print("测试集正例比例:", round(float(y_test.mean()), 4))
table
