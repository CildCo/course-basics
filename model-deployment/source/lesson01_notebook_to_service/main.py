from pathlib import Path
import json

import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from IPython.display import display

FEATURES = [
    "mean radius",
    "mean texture",
    "mean perimeter",
    "mean area",
    "mean smoothness",
    "mean concave points",
]

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

bunch = load_breast_cancer()
frame = pd.DataFrame(bunch.data, columns=bunch.feature_names)[FEATURES]
target = pd.Series(bunch.target, name="target")

X_train, X_test, y_train, y_test = train_test_split(
    frame, target, test_size=0.2, random_state=42, stratify=target
)

pipeline = Pipeline([
    ("scale", StandardScaler()),
    ("model", LogisticRegression(max_iter=1000, random_state=42)),
]).fit(X_train, y_train)

probability = pipeline.predict_proba(X_test)[:, 1]
print("训练样本:", X_train.shape, "测试样本:", X_test.shape)
print("特征数:", len(FEATURES))
print("测试集准确率:", round(accuracy_score(y_test, pipeline.predict(X_test)), 3))
print("测试集 ROC AUC:", round(roc_auc_score(y_test, probability), 3))
print("类别:", [str(name) for name in bunch.target_names])


contract = pd.DataFrame([
    {"字段": "mean_radius", "对应特征": FEATURES[0], "类型": "float", "约束": "0 < x <= 50", "示例": round(float(X_train.iloc[0, 0]), 3)},
    {"字段": "mean_texture", "对应特征": FEATURES[1], "类型": "float", "约束": "0 < x <= 60", "示例": round(float(X_train.iloc[0, 1]), 3)},
    {"字段": "mean_perimeter", "对应特征": FEATURES[2], "类型": "float", "约束": "0 < x <= 250", "示例": round(float(X_train.iloc[0, 2]), 3)},
    {"字段": "mean_area", "对应特征": FEATURES[3], "类型": "float", "约束": "0 < x <= 3000", "示例": round(float(X_train.iloc[0, 3]), 3)},
    {"字段": "mean_smoothness", "对应特征": FEATURES[4], "类型": "float", "约束": "0 < x <= 0.3", "示例": round(float(X_train.iloc[0, 4]), 3)},
    {"字段": "mean_concave_points", "对应特征": FEATURES[5], "类型": "float", "约束": "0 < x <= 0.3", "示例": round(float(X_train.iloc[0, 5]), 3)},
])
display(contract)

model_card = {
    "model_version": "0.1.0",
    "artifact": "breast_cancer_pipeline.joblib",
    "trained_at": "2026-10-25",
    "framework": f"scikit-learn {sklearn.__version__}",
    "features": FEATURES,
    "target": {"0": "malignant", "1": "benign"},
    "metrics": {
        "accuracy": round(accuracy_score(y_test, pipeline.predict(X_test)), 4),
        "roc_auc": round(roc_auc_score(y_test, probability), 4),
    },
}
(out / "model_card.json").write_text(
    json.dumps(model_card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("模型卡片:", (out / "model_card.json").relative_to(Path.cwd()).as_posix())
print(json.dumps(model_card, ensure_ascii=False, indent=2))
print("下一节会把 Pipeline 保存成", model_card["artifact"])


FIELD_MAP = {
    "mean_radius": "mean radius",
    "mean_texture": "mean texture",
    "mean_perimeter": "mean perimeter",
    "mean_area": "mean area",
    "mean_smoothness": "mean smoothness",
    "mean_concave_points": "mean concave points",
}

CONTRACT = {
    "mean_radius": (0.0, 50.0),
    "mean_texture": (0.0, 60.0),
    "mean_perimeter": (0.0, 250.0),
    "mean_area": (0.0, 3000.0),
    "mean_smoothness": (0.0, 0.3),
    "mean_concave_points": (0.0, 0.3),
}

def check_payload(payload):
    problems = []
    for field, (low, high) in CONTRACT.items():
        if field not in payload:
            problems.append(f"{field}: 缺少字段")
            continue
        value = payload[field]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            problems.append(f"{field}: 类型应为 float")
        elif not (low < value <= high):
            problems.append(f"{field}: 取值应在 ({low}, {high}]")
    extra = sorted(set(payload) - set(CONTRACT))
    return {"问题": problems, "多余字段": extra}

good = {api: float(X_test.iloc[0][column]) for api, column in FIELD_MAP.items()}
missing = {key: value for key, value in good.items() if key != "mean_area"}
negative = dict(good, mean_radius=-1.0)

for name, payload in [("正常请求", good), ("缺少字段", missing), ("负值", negative)]:
    print(name, "->", check_payload(payload))
