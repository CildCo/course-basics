import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir():
            return base
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        return here.parent


def data_path(name: str) -> Path:
    return course_root() / "assets" / name


def output_dir() -> Path:
    target = course_root() / "output"
    target.mkdir(parents=True, exist_ok=True)
    return target


print("课程目录:", course_root().name)
print("数据目录:", (course_root() / "assets").relative_to(course_root()).as_posix())
print("输出目录:", output_dir().relative_to(course_root()).as_posix())

from fastapi import FastAPI
from fastapi.testclient import TestClient


def build_app():
    app = FastAPI(title="版本示例")

    @app.get("/api/v1/orders/{order_id}")
    def get_order_v1(order_id: int):
        return {
            "id": order_id,
            "total": 128.0,
            "created": "2026-10-01 10:00",
        }

    @app.get("/api/v2/orders/{order_id}")
    def get_order_v2(order_id: int):
        return {
            "id": order_id,
            "total": {"amount": 128.0, "currency": "CNY"},
            "created_at": "2026-10-01T10:00:00+08:00",
        }

    return app


client = TestClient(build_app())
v1 = client.get("/api/v1/orders/1001")
v2 = client.get("/api/v2/orders/1001")
print("v1:", v1.status_code, v1.json())
print("v2:", v2.status_code, v2.json())
print("v1 字段都在 v2 中:", set(v1.json()) <= set(v2.json()))


import itertools

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="CNY", min_length=3, max_length=3)


def build_app():
    app = FastAPI(title="幂等支付")
    payments = {}
    idempotency = {}
    ids = itertools.count(1)

    @app.post("/api/v1/payments", status_code=201)
    def create_payment(
        payload: PaymentCreate,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ):
        if idempotency_key and idempotency_key in idempotency:
            return JSONResponse(
                status_code=200,
                content=idempotency[idempotency_key],
                headers={"Idempotency-Replayed": "true"},
            )
        payment = {
            "id": next(ids),
            "amount": payload.amount,
            "currency": payload.currency,
            "status": "pending",
        }
        payments[payment["id"]] = payment
        if idempotency_key:
            idempotency[idempotency_key] = payment
        return JSONResponse(status_code=201, content=payment)

    @app.get("/api/v1/payments")
    def list_payments():
        return {"items": list(payments.values()), "total": len(payments)}

    return app


client = TestClient(build_app())
headers = {"Idempotency-Key": "pay-20261025-001"}
first = client.post("/api/v1/payments", json={"amount": 99.0}, headers=headers)
second = client.post("/api/v1/payments", json={"amount": 99.0}, headers=headers)
third = client.post(
    "/api/v1/payments",
    json={"amount": 150.0},
    headers={"Idempotency-Key": "pay-20261025-002"},
)
print("第一次:", first.status_code, first.json())
print("重复提交:", second.status_code, second.headers.get("Idempotency-Replayed"), second.json())
print("新 key:", third.status_code, third.json())
print("实际支付单数:", client.get("/api/v1/payments").json()["total"])


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import Image, display

capacity = 5
refill_per_second = 2.0
tokens = float(capacity)
last_time = 0.0
arrivals = [0.1, 0.2, 0.3, 0.5, 0.9, 1.0, 1.2, 1.4, 1.6, 2.0, 2.3, 2.6, 3.0]
allowed = []
rejected = []
token_trace = []

for moment in arrivals:
    tokens = min(capacity, tokens + (moment - last_time) * refill_per_second)
    last_time = moment
    if tokens >= 1:
        tokens -= 1
        allowed.append(moment)
    else:
        rejected.append(moment)
    token_trace.append(tokens)

print("请求数:", len(arrivals))
print("放行:", len(allowed), "拒绝:", len(rejected))
print("拒绝时刻:", rejected)
print("第 10 个请求后的剩余令牌:", round(token_trace[9], 2))
print("429 响应示例:", {"status": 429, "Retry-After": "1", "error": {"code": "rate_limited", "message": "请求过于频繁"}})

fig, ax = plt.subplots(figsize=(7.5, 3.2))
ax.step(arrivals, token_trace, where="post", color="#3b6ea5", label="tokens left")
ax.scatter(allowed, [0.1] * len(allowed), color="#2f855a", label="allowed", zorder=3)
ax.scatter(rejected, [0.1] * len(rejected), color="#c53030", marker="x", label="rejected", zorder=3)
ax.set_ylim(0, capacity + 1)
ax.set_xlabel("time (s)")
ax.set_ylabel("tokens")
ax.set_title("Token bucket: capacity 5, refill 2/s")
ax.legend(loc="upper right", frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()

chart_path = output_dir() / "token-bucket.png"
fig.savefig(chart_path, dpi=120)
plt.close(fig)
display(Image(filename=str(chart_path)))
print("图表已写入:", chart_path.name)
