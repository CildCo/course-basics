import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

X_array, y_array = make_classification(
    n_samples=2500,
    n_features=10,
    n_informative=5,
    n_redundant=2,
    flip_y=0.15,
    class_sep=1.0,
    random_state=RANDOM_STATE,
)
X = pd.DataFrame(X_array, columns=[f"feature_{i:02d}" for i in range(1, 11)])
y = pd.Series(y_array, name="default")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)
print("训练集:", X_train.shape, "测试集:", X_test.shape)
print("违约比例:", round(float(y.mean()), 3))


logistic = Pipeline([
    ("scale", StandardScaler()),
    ("clf", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
])
naive_bayes = GaussianNB()
calibrated = CalibratedClassifierCV(
    estimator=GaussianNB(),
    method="sigmoid",
    cv=5,
)

rows = []
probs = {}
for name, model in [
    ("逻辑回归", logistic),
    ("高斯朴素贝叶斯", naive_bayes),
    ("朴素贝叶斯 + sigmoid 校准", calibrated),
]:
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    probs[name] = prob
    rows.append({
        "模型": name,
        "AUC": roc_auc_score(y_test, prob),
        "Brier 分数": brier_score_loss(y_test, prob),
        "LogLoss": log_loss(y_test, prob),
    })

pd.DataFrame(rows).round(4)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(6.5, 5))
colors = {"逻辑回归": "#5B7DB1", "高斯朴素贝叶斯": "#C97B63", "朴素贝叶斯 + sigmoid 校准": "#7FA88B"}
for name, prob in probs.items():
    fraction_positive, mean_predicted = calibration_curve(
        y_test, prob, n_bins=8, strategy="quantile"
    )
    ax.plot(mean_predicted, fraction_positive, marker="o", color=colors[name], label=name)

ax.plot([0, 1], [0, 1], linestyle="--", color="#888888", label="完美校准")
ax.set_xlabel("平均预测概率")
ax.set_ylabel("实际正例比例")
ax.set_title("可靠性图：预测概率是否可信")
ax.legend(frameon=False, fontsize=9)
ax.grid(alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "calibration.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "calibration.png")))
plt.close(fig)


rows = []
for name in ["高斯朴素贝叶斯", "朴素贝叶斯 + sigmoid 校准"]:
    fraction_positive, mean_predicted = calibration_curve(
        y_test, probs[name], n_bins=6, strategy="quantile"
    )
    for predicted, actual in zip(mean_predicted, fraction_positive):
        rows.append({
            "模型": name,
            "平均预测": round(float(predicted), 3),
            "实际比例": round(float(actual), 3),
            "偏差": round(float(actual - predicted), 3),
        })

pd.DataFrame(rows)
