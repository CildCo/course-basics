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
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

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
model_path = out / "model.joblib"
joblib.dump(pipeline, model_path)
probabilities = pipeline.predict_proba(X_test)[:, 1]
sample_index = int(np.argmin(np.abs(probabilities - 0.5)))

print("模型已保存:", model_path.name, model_path.stat().st_size, "字节")
print("测试样本:", X_test.shape)
print("展示样例概率:", round(float(probabilities[sample_index]), 4))


MODEL_VERSION = "1.0.0"
FEATURE_FIELDS = {
    "mean_radius": "mean radius",
    "mean_texture": "mean texture",
    "mean_perimeter": "mean perimeter",
    "mean_area": "mean area",
    "mean_smoothness": "mean smoothness",
    "mean_concave_points": "mean concave points",
}

class PredictRequest(BaseModel):
    mean_radius: float = Field(gt=0, le=50, description="平均半径")
    mean_texture: float = Field(gt=0, le=60, description="平均纹理")
    mean_perimeter: float = Field(gt=0, le=250, description="平均周长")
    mean_area: float = Field(gt=0, le=3000, description="平均面积")
    mean_smoothness: float = Field(gt=0, le=0.3, description="平均平滑度")
    mean_concave_points: float = Field(gt=0, le=0.3, description="平均凹点")
    request_id: str | None = None

class PredictResponse(BaseModel):
    request_id: str
    prediction: int
    label: str
    probability: float
    model_version: str
    latency_ms: float

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

print("应用:", app.title)
print("路由:", sorted(route.path for route in app.routes if route.path.startswith("/")))


client = TestClient(app)
payload = {
    field: round(float(X_test.iloc[sample_index][column]), 4)
    for field, column in FEATURE_FIELDS.items()
}

response = client.post("/predict", json=payload)
print("状态码:", response.status_code)
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
print("健康检查:", client.get("/health").json())


cases = {
    "缺少字段": {key: value for key, value in payload.items() if key != "mean_area"},
    "负值": {**payload, "mean_radius": -1.0},
    "类型错误": {**payload, "mean_texture": "abc"},
}

for name, body in cases.items():
    response = client.post("/predict", json=body)
    detail = response.json()["detail"][0]
    print(f"{name} -> {response.status_code} {detail['loc']} {detail['msg']}")
