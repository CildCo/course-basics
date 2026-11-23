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

bunch = load_breast_cancer()
frame = pd.DataFrame(bunch.data, columns=bunch.feature_names)[FEATURES]
target = pd.Series(bunch.target, name="target")
X_train, X_test, y_train, y_test = train_test_split(
    frame, target, test_size=0.2, random_state=42, stratify=target
)

def build(version):
    if version == "v1":
        estimator = LogisticRegression(max_iter=1000, random_state=42)
    else:
        estimator = LogisticRegression(max_iter=1000, random_state=42, C=0.001)
    return Pipeline([
        ("scale", StandardScaler()),
        ("model", estimator),
    ]).fit(X_train, y_train)

registry = Path.cwd() / "output" / "registry"
rows = []
for version in ["v1", "v2"]:
    pipeline = build(version)
    version_dir = registry / version
    version_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, version_dir / "model.joblib")
    probability = pipeline.predict_proba(X_test)[:, 1]
    meta = {
        "version": version,
        "artifact": "model.joblib",
        "trained_at": "2026-10-25",
        "sklearn_version": sklearn_version,
        "features": FEATURES,
        "accuracy": round(accuracy_score(y_test, pipeline.predict(X_test)), 4),
        "roc_auc": round(roc_auc_score(y_test, probability), 4),
    }
    (version_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    rows.append(meta)

print(pd.DataFrame(rows)[["version", "accuracy", "roc_auc"]].to_string(index=False))
print("注册目录:", registry.relative_to(Path.cwd()).as_posix())


class ModelRouter:
    def __init__(self, registry_dir, stable="v1", canary="v2", canary_percent=10):
        self.stable = stable
        self.canary = canary
        self.canary_percent = canary_percent
        self.models = {
            version: joblib.load(Path(registry_dir) / version / "model.joblib")
            for version in (stable, canary)
        }

    def pick(self, user_id):
        if not self.canary or self.canary_percent <= 0:
            return self.stable
        bucket = int(hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:8], 16) % 100
        return self.canary if bucket < self.canary_percent else self.stable

    def predict(self, user_id, row):
        version = self.pick(user_id)
        probability = float(self.models[version].predict_proba(row)[0, 1])
        return {
            "version": version,
            "prediction": int(probability >= 0.5),
            "probability": round(probability, 4),
        }

router = ModelRouter(registry, canary_percent=10)
users = [f"user-{index:04d}" for index in range(2000)]
before = pd.Series([router.pick(user) for user in users]).value_counts().reindex(
    ["v1", "v2"], fill_value=0
)
print("灰度 10% 的用户路由:")
print(before.to_string())
print("v2 实际占比:", round(before["v2"] / len(users), 3))

router.canary_percent = 0
after = pd.Series([router.pick(user) for user in users]).value_counts().reindex(
    ["v1", "v2"], fill_value=0
)
print("\n回滚后的用户路由:")
print(after.to_string())


import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

labels = ["灰度 10%", "回滚后"]
v1_counts = [int(before["v1"]), int(after["v1"])]
v2_counts = [int(before["v2"]), int(after["v2"])]
x = np.arange(len(labels))

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.bar(x - 0.2, v1_counts, width=0.4, label="v1 稳定版", color="#4C78A8")
ax.bar(x + 0.2, v2_counts, width=0.4, label="v2 灰度版", color="#F58518")
ax.set_xticks(x, labels)
ax.set_ylabel("路由用户数")
ax.set_title("灰度切流与回滚")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
figure_path = Path.cwd() / "output" / "canary.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)


decision = pd.DataFrame(rows)[["version", "accuracy", "roc_auc"]].copy()
decision["角色"] = ["稳定版", "灰度版"]
decision["当前流量"] = [f"{before['v1'] / len(users):.0%}", f"{before['v2'] / len(users):.0%}"]
decision["回滚后流量"] = [f"{after['v1'] / len(users):.0%}", f"{after['v2'] / len(users):.0%}"]
display(decision)

print("本次结论：v2 准确率低于 v1，保持 canary_percent = 0")
print("灰度规则：新版本指标不低于稳定版、错误率稳定后，再把 canary_percent 调到 100")
print("回滚动作：canary_percent = 0，全部流量回到", router.stable)
