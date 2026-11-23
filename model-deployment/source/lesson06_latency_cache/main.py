from pathlib import Path
import time
from functools import lru_cache

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

def predict_one(values):
    row = pd.DataFrame([values], columns=FEATURES)
    return float(pipeline.predict_proba(row)[0, 1])

sample_index = int(np.argmin(np.abs(pipeline.predict_proba(X_test)[:, 1] - 0.5)))
sample = X_test.iloc[sample_index].to_numpy()
print("样例预测:", round(predict_one(sample), 4))


latencies = []
for _ in range(300):
    start = time.perf_counter()
    predict_one(sample)
    latencies.append((time.perf_counter() - start) * 1000)
latencies = np.array(latencies)

summary = pd.DataFrame([{
    "请求数": len(latencies),
    "平均 ms": round(float(latencies.mean()), 3),
    "p50 ms": round(float(np.percentile(latencies, 50)), 3),
    "p95 ms": round(float(np.percentile(latencies, 95)), 3),
    "p99 ms": round(float(np.percentile(latencies, 99)), 3),
    "吞吐 次/秒": round(1000 / float(latencies.mean()), 1),
}])
display(summary)


batch_rows = []
for size in [1, 8, 32, 64]:
    batch = pd.DataFrame(np.tile(sample, (size, 1)), columns=FEATURES)
    runs = []
    for _ in range(20):
        start = time.perf_counter()
        pipeline.predict_proba(batch)
        runs.append((time.perf_counter() - start) * 1000)
    total_ms = float(np.mean(runs))
    batch_rows.append({
        "批量大小": size,
        "总耗时 ms": round(total_ms, 3),
        "每次请求 ms": round(total_ms / size, 4),
    })
display(pd.DataFrame(batch_rows))


@lru_cache(maxsize=512)
def cached_predict(values):
    return predict_one(np.array(values))

rng = np.random.default_rng(42)
pool = [tuple(np.round(row, 4)) for row in X_test.head(50).to_numpy()]
requests = []
for _ in range(400):
    if rng.random() < 0.8:
        requests.append(pool[int(rng.integers(0, len(pool)))])
    else:
        row = X_test.sample(1, random_state=int(rng.integers(0, 10**6))).iloc[0]
        requests.append(tuple(np.round(row.to_numpy(), 4)))

start = time.perf_counter()
for values in requests:
    predict_one(np.array(values))
uncached_ms = (time.perf_counter() - start) * 1000

cached_predict.cache_clear()
start = time.perf_counter()
for values in requests:
    cached_predict(values)
cached_ms = (time.perf_counter() - start) * 1000
info = cached_predict.cache_info()

print("请求数:", len(requests))
print("未缓存总耗时 ms:", round(uncached_ms, 1))
print("缓存后总耗时 ms:", round(cached_ms, 1))
print("加速比:", round(uncached_ms / cached_ms, 2))
print("缓存命中率:", round(info.hits / (info.hits + info.misses), 3))


import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(latencies, bins=25, color="#4C78A8", alpha=0.85)
axes[0].set_title("单次推理延迟分布")
axes[0].set_xlabel("毫秒")
axes[0].set_ylabel("次数")

sizes = [row["批量大小"] for row in batch_rows]
per_request = [row["每次请求 ms"] for row in batch_rows]
axes[1].plot(sizes, per_request, marker="o", color="#F58518")
axes[1].set_title("批量越大，每次请求开销越低")
axes[1].set_xlabel("批量大小")
axes[1].set_ylabel("每次请求毫秒")
axes[1].set_xticks(sizes)
for axis in axes:
    axis.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
figure_path = Path.cwd() / "output" / "latency-cache.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
