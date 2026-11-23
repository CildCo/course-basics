from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn import __version__ as sklearn_version

FEATURES = [
    "mean radius",
    "mean texture",
    "mean perimeter",
    "mean area",
    "mean smoothness",
    "mean concave points",
]

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

model_path = out / "breast_cancer_pipeline.joblib"
joblib.dump(pipeline, model_path)
digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
probability = pipeline.predict_proba(X_test)[:, 1]

metadata = {
    "model_version": "1.0.0",
    "artifact": model_path.name,
    "sha256": digest,
    "features": FEATURES,
    "target": {"0": "malignant", "1": "benign"},
    "sklearn_version": sklearn_version,
    "trained_at": "2026-10-25",
    "metrics": {
        "accuracy": round(accuracy_score(y_test, pipeline.predict(X_test)), 4),
        "roc_auc": round(roc_auc_score(y_test, probability), 4),
    },
}
(out / "model_meta.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print("模型文件:", model_path.name)
print("文件大小:", model_path.stat().st_size, "字节")
print("SHA256 前缀:", digest[:16])
print("测试集准确率:", metadata["metrics"]["accuracy"])


loaded = joblib.load(model_path)
before = pipeline.predict_proba(X_test)[:, 1]
after = loaded.predict_proba(X_test)[:, 1]
sample_index = int(np.argmin(np.abs(before - 0.5)))
sample = X_test.iloc[[sample_index]]

print("加载后最大预测差异:", float(np.max(np.abs(before - after))))
print("标签完全一致:", bool(np.array_equal(pipeline.predict(X_test), loaded.predict(X_test))))
print("样本:", {name: round(float(value), 3) for name, value in sample.iloc[0].items()})
print("预测标签:", int(loaded.predict(sample)[0]))
print("预测概率:", round(float(loaded.predict_proba(sample)[0, 1]), 4))


shuffled = X_test[FEATURES[::-1]].copy()
shuffled.columns = FEATURES
changed = int(np.sum(pipeline.predict(X_test) != pipeline.predict(shuffled)))

print("特征顺序:", FEATURES)
print("打乱列顺序后预测改变的样本:", changed, "/", len(X_test))
print("打乱后的样例:", {name: round(float(value), 3) for name, value in shuffled.iloc[0].items()})
print("元数据文件:", (out / "model_meta.json").relative_to(Path.cwd()).as_posix())
