from typing import Literal

from fastapi import FastAPI, Path, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI()


@app.get("/items/{item_id}")
def get_item(
    item_id: int = Path(ge=1, description="商品编号"),
    q: str | None = Query(default=None, max_length=20),
):
    return {"item_id": item_id, "q": q}


@app.get("/items")
def list_items(
    limit: int = Query(default=10, ge=1, le=50),
    sort: Literal["new", "price"] = "new",
):
    return {"limit": limit, "sort": sort}


class Order(BaseModel):
    product: str = Field(min_length=1)
    units: int = Field(gt=0)


@app.post("/orders")
def create_order(order: Order, dry_run: bool = False):
    return {"order": order.model_dump(), "dry_run": dry_run}


client = TestClient(app)
print("应用已就绪")


print("路径参数:", client.get("/items/7?q=键盘").json())
print("编号非法:", client.get("/items/0").status_code)
print("类型错误:", client.get("/items/abc").status_code)


print("默认:", client.get("/items").json())
print("分页 + 排序:", client.get("/items?limit=5&sort=price").json())
print("超出上限:", client.get("/items?limit=999").status_code)
print("非法排序:", client.get("/items?sort=random").status_code)


created = client.post("/orders", json={"product": "显示器", "units": 2})
print("创建订单:", created.status_code, created.json())

dry = client.post("/orders?dry_run=true", json={"product": "显示器", "units": 2})
print("预演:", dry.status_code, dry.json())

missing = client.post("/orders", json={"product": "显示器"})
print("缺字段:", missing.status_code)
print(missing.json()["detail"][0]["loc"], missing.json()["detail"][0]["msg"])
