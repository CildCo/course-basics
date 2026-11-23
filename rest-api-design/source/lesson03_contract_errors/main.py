import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class OrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=3, max_length=20)
    quantity: int = Field(ge=1, le=99)
    unit_price: float = Field(gt=0)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=3, max_length=20)
    items: list[OrderItem] = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=200)

    @field_validator("customer_id")
    @classmethod
    def customer_id_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("customer_id 不能为空")
        return value


class OrderOut(BaseModel):
    id: int
    customer_id: str
    items: list[OrderItem]
    total: float
    status: str


valid = OrderCreate(
    customer_id="C-1001",
    items=[{"sku": "A-01", "quantity": 2, "unit_price": 39.5}],
    note="工作日送达",
)
print("校验通过:", valid.model_dump())
print("序列化:", valid.model_dump_json())

try:
    OrderCreate(
        customer_id="   ",
        items=[{"sku": "A", "quantity": 0, "unit_price": -1, "color": "red"}],
        extra_field="not allowed",
    )
except ValidationError as exc:
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        print(f"{field:<28}{error['type']:<22}{error['msg']}")


import itertools

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_body(code, message, fields=None, request_id="req-local"):
    body = {"error": {"code": code, "message": message}}
    if fields is not None:
        body["error"]["fields"] = fields
    body["error"]["request_id"] = request_id
    return body


orders = {}
order_ids = itertools.count(1)


def build_app():
    app = FastAPI(title="订单接口")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request, exc):
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code,
                str(exc.detail),
                request_id=request.headers.get("X-Request-Id", "req-local"),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request, exc):
        fields = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_body(
                "validation_error",
                "请求参数不合法",
                fields=fields,
                request_id=request.headers.get("X-Request-Id", "req-local"),
            ),
        )

    @app.post("/api/v1/orders", response_model=OrderOut, status_code=201)
    def create_order(payload: OrderCreate):
        total = round(sum(item.quantity * item.unit_price for item in payload.items), 2)
        order = {
            "id": next(order_ids),
            "customer_id": payload.customer_id,
            "items": [item.model_dump() for item in payload.items],
            "total": total,
            "status": "created",
        }
        orders[order["id"]] = order
        return order

    @app.get("/api/v1/orders/{order_id}", response_model=OrderOut)
    def get_order(order_id: int):
        if order_id not in orders:
            raise HTTPException(status_code=404, detail="订单不存在")
        return orders[order_id]

    return app


client = TestClient(build_app())
paths = [route.path for route in client.app.routes if route.path.startswith("/api")]
print("注册路由:", paths)


import json

created = client.post(
    "/api/v1/orders",
    json={
        "customer_id": "C-1001",
        "items": [{"sku": "A-01", "quantity": 2, "unit_price": 39.5}],
        "note": "工作日送达",
    },
    headers={"X-Request-Id": "req-1001"},
)
print("创建:", created.status_code, "id =", created.json()["id"], "total =", created.json()["total"])

bad = client.post(
    "/api/v1/orders",
    json={
        "customer_id": "C-1002",
        "items": [{"sku": "B", "quantity": 0, "unit_price": 0}],
        "unexpected": True,
    },
    headers={"X-Request-Id": "req-1002"},
)
print("校验失败:", bad.status_code)
print(json.dumps(bad.json(), ensure_ascii=False, indent=2))

missing = client.get("/api/v1/orders/999", headers={"X-Request-Id": "req-1003"})
print("不存在:", missing.status_code, json.dumps(missing.json(), ensure_ascii=False))

unknown = client.get("/api/v1/payments", headers={"X-Request-Id": "req-1004"})
print("未知路径:", unknown.status_code, json.dumps(unknown.json(), ensure_ascii=False))


class UserOut(BaseModel):
    id: int
    name: str


internal_user = {
    "id": 5,
    "name": "陈晓",
    "password_hash": "not-for-client",
    "internal_score": 88,
}
public = UserOut(**internal_user)
print("内部字段:", sorted(internal_user))
print("响应模型字段:", sorted(public.model_dump()))
print("返回给客户端:", public.model_dump())
