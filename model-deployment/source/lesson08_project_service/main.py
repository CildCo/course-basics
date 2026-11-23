from pathlib import Path
import json
import os
import subprocess
import sys

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
service_dir = out / "service"
service_dir.mkdir(exist_ok=True)

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
joblib.dump(pipeline, service_dir / "model.joblib")

probability = pipeline.predict_proba(X_test)[:, 1]
metadata = {
    "model_version": "1.0.0",
    "artifact": "model.joblib",
    "features": FEATURES,
    "sklearn_version": sklearn_version,
    "trained_at": "2026-10-25",
    "metrics": {
        "accuracy": round(accuracy_score(y_test, pipeline.predict(X_test)), 4),
        "roc_auc": round(roc_auc_score(y_test, probability), 4),
    },
}
(service_dir / "model_meta.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print("服务目录:", service_dir.relative_to(Path.cwd()).as_posix())
print("模型大小:", (service_dir / "model.joblib").stat().st_size, "字节")
print("模型版本:", metadata["model_version"], "准确率:", metadata["metrics"]["accuracy"])


SERVICE_CODE = """from pathlib import Path
import time

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent
MODEL_VERSION = "1.0.0"
MAX_BATCH = 32
FEATURE_FIELDS = {
    "mean_radius": "mean radius",
    "mean_texture": "mean texture",
    "mean_perimeter": "mean perimeter",
    "mean_area": "mean area",
    "mean_smoothness": "mean smoothness",
    "mean_concave_points": "mean concave points",
}

pipeline = joblib.load(BASE_DIR / "model.joblib")

class PredictRequest(BaseModel):
    mean_radius: float = Field(gt=0, le=50)
    mean_texture: float = Field(gt=0, le=60)
    mean_perimeter: float = Field(gt=0, le=250)
    mean_area: float = Field(gt=0, le=3000)
    mean_smoothness: float = Field(gt=0, le=0.3)
    mean_concave_points: float = Field(gt=0, le=0.3)
    request_id: str | None = None

class PredictResponse(BaseModel):
    request_id: str
    prediction: int
    label: str
    probability: float
    model_version: str
    latency_ms: float

class BatchRequest(BaseModel):
    items: list[dict] = Field(min_length=1)

app = FastAPI(title="乳腺癌风险评分服务", version=MODEL_VERSION)

def infer(item):
    frame = pd.DataFrame(
        [[getattr(item, field) for field in FEATURE_FIELDS]],
        columns=list(FEATURE_FIELDS.values()),
    )
    probability = float(pipeline.predict_proba(frame)[0, 1])
    label = "benign" if probability >= 0.5 else "malignant"
    return probability, label

@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}

@app.post("/predict", response_model=PredictResponse)
def predict(item: PredictRequest):
    start = time.perf_counter()
    probability, label = infer(item)
    elapsed = (time.perf_counter() - start) * 1000
    return PredictResponse(
        request_id=item.request_id or f"req-{time.time_ns()}",
        prediction=int(probability >= 0.5),
        label=label,
        probability=round(probability, 4),
        model_version=MODEL_VERSION,
        latency_ms=round(elapsed, 3),
    )

@app.post("/predict/batch")
def predict_batch(batch: BatchRequest):
    if len(batch.items) > MAX_BATCH:
        raise HTTPException(status_code=413, detail=f"单次最多 {MAX_BATCH} 条")
    results = []
    for index, raw in enumerate(batch.items):
        try:
            item = PredictRequest(**raw)
        except ValidationError as exc:
            first = exc.errors()[0]
            results.append({
                "index": index,
                "status": "error",
                "field": ".".join(str(part) for part in first["loc"]),
                "detail": first["msg"],
            })
            continue
        probability, label = infer(item)
        results.append({
            "index": index,
            "status": "ok",
            "prediction": int(probability >= 0.5),
            "label": label,
            "probability": round(probability, 4),
        })
    return {
        "count": len(results),
        "ok": sum(row["status"] == "ok" for row in results),
        "failed": sum(row["status"] == "error" for row in results),
        "items": results,
    }
"""

(service_dir / "app.py").write_text(SERVICE_CODE, encoding="utf-8")
print("已写入 app.py，行数:", len(SERVICE_CODE.splitlines()))


TEST_CODE = """import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)
PAYLOAD = {
    "mean_radius": 14.2,
    "mean_texture": 20.1,
    "mean_perimeter": 92.0,
    "mean_area": 650.0,
    "mean_smoothness": 0.09,
    "mean_concave_points": 0.05,
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["model_version"] == "1.0.0"


def test_predict_ok():
    response = client.post("/predict", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["label"] in {"benign", "malignant"}
    assert 0 <= body["probability"] <= 1


def test_predict_missing_field():
    body = dict(PAYLOAD)
    body.pop("mean_area")
    response = client.post("/predict", json=body)
    assert response.status_code == 422


def test_batch_partial_failure():
    bad = dict(PAYLOAD)
    bad["mean_radius"] = -1
    response = client.post("/predict/batch", json={"items": [PAYLOAD, bad, PAYLOAD]})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] == 2
    assert body["failed"] == 1


def test_batch_too_large():
    response = client.post("/predict/batch", json={"items": [PAYLOAD] * 33})
    assert response.status_code == 413
"""

(service_dir / "test_app.py").write_text(TEST_CODE, encoding="utf-8")
print("已写入 test_app.py")
print("目录内容:", sorted(path.name for path in service_dir.iterdir()))


result = subprocess.run(
    [sys.executable, "-m", "pytest", "test_app.py", "-q", "--color=no", "-p", "no:cacheprovider"],
    cwd=service_dir,
    capture_output=True,
    text=True,
    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
)
print(result.stdout.strip())
if result.returncode != 0:
    print(result.stderr.strip())
    raise RuntimeError("pytest 未通过")
print("pytest 退出码:", result.returncode)

report = {
    "service": "breast-cancer-risk",
    "model_version": metadata["model_version"],
    "tests": 5,
    "result": "passed",
    "transport": "TestClient（进程内，无端口）",
}
(out / "acceptance.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("验收报告:", (out / "acceptance.json").relative_to(Path.cwd()).as_posix())


from fastapi.testclient import TestClient

sys.path.insert(0, str(service_dir))
import app as service

client = TestClient(service.app)
payload = {
    "mean_radius": 14.2,
    "mean_texture": 20.1,
    "mean_perimeter": 92.0,
    "mean_area": 650.0,
    "mean_smoothness": 0.09,
    "mean_concave_points": 0.05,
}

print("健康检查:", client.get("/health").json())
single = client.post("/predict", json=payload)
print("单条推理:", json.dumps(single.json(), ensure_ascii=False))
batch = client.post(
    "/predict/batch",
    json={"items": [payload, {**payload, "mean_texture": -3.0}, payload]},
)
body = batch.json()
print("批量汇总:", {key: body[key] for key in ["count", "ok", "failed"]})
print("失败条目:", body["items"][1])
