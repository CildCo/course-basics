import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

cancer = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    cancer.data, cancer.target, test_size=0.2, random_state=42, stratify=cancer.target
)

base = make_pipeline(
    StandardScaler(),
    LogisticRegression(max_iter=5000, random_state=42),
)
scores = cross_val_score(base, X_train, y_train, cv=5, scoring="roc_auc")

print("每折 AUC:", np.round(scores, 3))
print("平均 AUC:", round(scores.mean(), 3))
print("标准差:", round(scores.std(), 3))


from sklearn.model_selection import GridSearchCV

param_grid = {"logisticregression__C": [0.01, 0.1, 1, 10]}
grid = GridSearchCV(base, param_grid, cv=5, scoring="roc_auc", n_jobs=1)
grid.fit(X_train, y_train)

print("最佳参数:", grid.best_params_)
print("最佳交叉验证 AUC:", round(grid.best_score_, 3))


from sklearn.metrics import accuracy_score, roc_auc_score

best = grid.best_estimator_
test_proba = best.predict_proba(X_test)[:, 1]
test_pred = best.predict(X_test)

print("测试集 AUC:", round(roc_auc_score(y_test, test_proba), 3))
print("测试集准确率:", round(accuracy_score(y_test, test_pred), 3))


import pandas as pd

results = pd.DataFrame(grid.cv_results_)
columns = [
    "param_logisticregression__C",
    "mean_test_score",
    "std_test_score",
    "rank_test_score",
]
print(results[columns].sort_values("rank_test_score").to_string(index=False))
