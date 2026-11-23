from pathlib import Path
import json

import numpy as np
import pandas as pd
import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
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
joblib.dump(pipeline, out / "model.joblib")

requests = pd.read_csv(data_path("recent_requests.csv"))
print("请求日志:", requests.shape)
print(requests["status"].value_counts().to_string())
print()
print(requests.head(3).to_string(index=False))


requests["is_error"] = requests["status"] != "ok"
error_rate = float(requests["is_error"].mean())
latency = requests.loc[requests["status"] == "ok", "latency_ms"]

valid = requests.dropna(subset=FEATURES).copy()
valid["probability"] = pipeline.predict_proba(valid[FEATURES])[:, 1]
valid["prediction"] = (valid["probability"] >= 0.5).astype(int)

print("请求总数:", len(requests))
print("错误率:", f"{error_rate:.1%}", "（", int(requests["is_error"].sum()), "条）")
print("成功请求延迟 p50/p95/p99:",
      [round(float(np.percentile(latency, q)), 1) for q in (50, 95, 99)], "ms")
print("有效输入:", len(valid), "条")
print(valid[["request_id", "probability", "prediction"]].head(3).to_string(index=False))


def psi(reference, current, bins=10):
    edges = np.quantile(reference, np.linspace(0, 1, bins + 1))
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)
    expected = np.histogram(reference, bins=edges)[0] / len(reference)
    actual = np.histogram(current, bins=edges)[0] / len(current)
    expected = np.clip(expected, 1e-6, None)
    actual = np.clip(actual, 1e-6, None)
    return float(np.sum((actual - expected) * np.log(actual / expected)))

def level(value):
    if value >= 0.2:
        return "漂移"
    if value >= 0.1:
        return "观察"
    return "稳定"

rows = []
for column in FEATURES:
    value = psi(X_train[column].to_numpy(), valid[column].to_numpy())
    rows.append({"特征": column, "PSI": round(value, 3), "判断": level(value)})
drift = pd.DataFrame(rows).sort_values("PSI", ascending=False).reset_index(drop=True)
display(drift)
print("最大 PSI:", drift.iloc[0]["PSI"], "特征:", drift.iloc[0]["特征"])


import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

top_feature = drift.iloc[0]["特征"]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(X_train[top_feature], bins=20, density=True, alpha=0.55,
        label="训练分布", color="#4C78A8")
ax.hist(valid[top_feature], bins=20, density=True, alpha=0.55,
        label="线上分布", color="#F58518")
ax.set_title(f"输入漂移：{top_feature}")
ax.set_xlabel(top_feature)
ax.set_ylabel("密度")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
figure_path = Path.cwd() / "output" / "drift.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)


alerts = []
if error_rate > 0.02:
    alerts.append(f"错误率 {error_rate:.1%} 超过 2%")
if drift.iloc[0]["PSI"] >= 0.2:
    alerts.append(f"{drift.iloc[0]['特征']} 的 PSI={drift.iloc[0]['PSI']} 超过 0.2")

monitor_report = {
    "requests": int(len(requests)),
    "error_rate": round(error_rate, 4),
    "p95_latency_ms": round(float(np.percentile(latency, 95)), 1),
    "max_psi": float(drift.iloc[0]["PSI"]),
    "alerts": alerts,
}
(out / "monitor_report.json").write_text(
    json.dumps(monitor_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("监控报告:", (out / "monitor_report.json").relative_to(Path.cwd()).as_posix())
print(json.dumps(monitor_report, ensure_ascii=False, indent=2))
print("\n告警:")
for item in alerts:
    print("-", item)
print("\n建议：先看错误明细，再抽样核对漂移特征的采集口径；确认是真实变化后再考虑重训。")
