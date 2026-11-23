import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

cancer = load_breast_cancer()
df = pd.DataFrame(cancer.data, columns=cancer.feature_names)
X_train, X_test, y_train, y_test = train_test_split(
    df, cancer.target, test_size=0.2, random_state=42, stratify=cancer.target
)

print("样本数:", len(df), "特征数:", df.shape[1])
print("训练集:", X_train.shape[0], "测试集:", X_test.shape[0])
print("训练集类别分布:", np.bincount(y_train))
print("测试集类别分布:", np.bincount(y_test))


from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

pipeline = Pipeline([
    ("scale", StandardScaler()),
    ("model", LogisticRegression(max_iter=5000, random_state=42)),
])
param_grid = {"model__C": [0.01, 0.1, 1, 10]}
grid = GridSearchCV(pipeline, param_grid, cv=5, scoring="roc_auc", n_jobs=1)
grid.fit(X_train, y_train)

print("最佳参数:", grid.best_params_)
print("交叉验证 AUC:", round(grid.best_score_, 3))


from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

best = grid.best_estimator_
pred = best.predict(X_test)
proba = best.predict_proba(X_test)[:, 1]

metrics = {
    "accuracy": accuracy_score(y_test, pred),
    "precision": precision_score(y_test, pred),
    "recall": recall_score(y_test, pred),
    "f1": f1_score(y_test, pred),
    "roc_auc": roc_auc_score(y_test, proba),
}
for name, value in metrics.items():
    print(f"{name}: {value:.3f}")
print("混淆矩阵:")
print(confusion_matrix(y_test, pred))


output_dir = Path.cwd() / "output"
output_dir.mkdir(exist_ok=True)
model_path = output_dir / "breast_cancer_pipeline.joblib"
joblib.dump(best, model_path)

report = {
    "dataset": "sklearn breast_cancer",
    "samples": int(len(df)),
    "features": int(df.shape[1]),
    "best_params": grid.best_params_,
    "cv_auc": round(float(grid.best_score_), 3),
    "test_metrics": {name: round(float(value), 3) for name, value in metrics.items()},
    "conclusion": "标准化加逻辑回归在测试集上取得较高 AUC，可以作为良恶性初筛的基线模型。",
    "limitations": [
        "数据只有 569 条，来自单一数据集，不能代表其他医院或设备。",
        "默认 0.5 阈值未按实际漏报/误报成本调整。",
        "特征为人工测量的细胞核指标，未覆盖影像或病史信息。",
        "未做外部验证和时间外推，上线前需要独立数据集复测。",
    ],
}
report_path = output_dir / "report.json"
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("模型:", model_path.relative_to(Path.cwd()).as_posix())
print("报告:", report_path.relative_to(Path.cwd()).as_posix())
print(json.dumps(report, ensure_ascii=False, indent=2))
