from pathlib import Path
import json
import time
import uuid

import numpy as np
import pandas as pd
import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError

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
probabilities = pipeline.predict_proba(X_test)[:, 1]
sample_index = int(np.argmin(np.abs(probabilities - 0.5)))

print("模型就绪，测试样本:", X_test.shape)
print("展示样例概率:", round(float(probabilities[sample_index]), 4))


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

app = FastAPI(title="乳腺癌风险评分", version=MODEL_VERSION)

def infer(item):
    row = pd.DataFrame(
        [[getattr(item, field) for field in FEATURE_FIELDS]],
        columns=list(FEATURE_FIELDS.values()),
    )
    return float(pipeline.predict_proba(row)[0, 1])

@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}

@app.post("/predict", response_model=PredictResponse)
def predict(item: PredictRequest):
    start = time.perf_counter()
    probability = infer(item)
    elapsed = (time.perf_counter() - start) * 1000
    return PredictResponse(
        request_id=item.request_id or f"req-{uuid.uuid4().hex[:10]}",
        prediction=int(probability >= 0.5),
        label="benign" if probability >= 0.5 else "malignant",
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
        probability = infer(item)
        results.append({
            "index": index,
            "status": "ok",
            "prediction": int(probability >= 0.5),
            "probability": round(probability, 4),
        })
    return {
        "count": len(results),
        "ok": sum(row["status"] == "ok" for row in results),
        "failed": sum(row["status"] == "error" for row in results),
        "items": results,
    }

print("单条上限: 1 条；批量上限:", MAX_BATCH, "条")


client = TestClient(app)
good = {
    field: round(float(X_test.iloc[sample_index][column]), 4)
    for field, column in FEATURE_FIELDS.items()
}

single = client.post("/predict", json=good)
print("单条:", single.status_code, json.dumps(single.json(), ensure_ascii=False))

mixed = {
    "items": [
        good,
        {**good, "mean_radius": -2.0},
        {key: value for key, value in good.items() if key != "mean_texture"},
        good,
    ]
}
batch = client.post("/predict/batch", json=mixed)
print("\n混合批量状态码:", batch.status_code)
print(json.dumps(batch.json(), ensure_ascii=False, indent=2))


too_many = {"items": [good] * (MAX_BATCH + 1)}
over = client.post("/predict/batch", json=too_many)
print("超限:", over.status_code, over.json()["detail"])

empty = client.post("/predict/batch", json={"items": []})
print("空批量:", empty.status_code, empty.json()["detail"][0]["msg"])

broken = client.post("/predict/batch", json={"items": "not-a-list"})
print("结构错误:", broken.status_code, broken.json()["detail"][0]["msg"])
