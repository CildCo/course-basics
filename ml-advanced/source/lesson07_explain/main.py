import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(1 - data.target, name="malignant")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)

forest = RandomForestClassifier(
    n_estimators=300, min_samples_leaf=2,
    random_state=RANDOM_STATE, n_jobs=1,
)
forest.fit(X_train, y_train)
print("训练完成，特征数:", X.shape[1])


perm = permutation_importance(
    forest, X_test, y_test,
    n_repeats=10, random_state=RANDOM_STATE,
    scoring="roc_auc", n_jobs=1,
)

importance = pd.DataFrame({
    "特征": X.columns,
    "不纯度重要性": forest.feature_importances_,
    "置换重要性": perm.importances_mean,
    "置换波动": perm.importances_std,
}).sort_values("置换重要性", ascending=False)

importance.head(10).round(4)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

top_features = importance["特征"].head(2).tolist()
disp = PartialDependenceDisplay.from_estimator(
    forest, X_test, features=top_features,
    kind="average", grid_resolution=40, n_cols=2,
)
fig = plt.gcf()
fig.set_size_inches(9, 3.8)
fig.suptitle("部分依赖：特征取值与恶性概率", y=1.02)
fig.tight_layout()
fig.savefig(OUTPUT / "partial-dependence.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "partial-dependence.png")))
plt.close(fig)
print("展示特征:", top_features)


X_dup = X.copy()
X_dup["worst radius（副本）"] = X_dup["worst radius"]
Xd_train, Xd_test, yd_train, yd_test = train_test_split(
    X_dup, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)
forest_dup = RandomForestClassifier(
    n_estimators=300, min_samples_leaf=2,
    random_state=RANDOM_STATE, n_jobs=1,
)
forest_dup.fit(Xd_train, yd_train)

dup_table = pd.DataFrame({
    "特征": X_dup.columns,
    "复制后不纯度重要性": forest_dup.feature_importances_,
})
dup_table[dup_table["特征"].isin(["worst radius", "worst radius（副本）"])].round(4)
