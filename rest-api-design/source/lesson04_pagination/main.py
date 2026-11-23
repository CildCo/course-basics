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

import json

orders = json.loads(data_path("orders.json").read_text(encoding="utf-8"))
status_count = {}
for order in orders:
    status_count[order["status"]] = status_count.get(order["status"], 0) + 1
print("订单数:", len(orders))
print("字段:", ", ".join(orders[0].keys()))
print("状态分布:", dict(sorted(status_count.items())))


import math

from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel


class OrderRow(BaseModel):
    id: int
    customer: str
    status: str
    amount: float
    created_at: str


class OrderPage(BaseModel):
    items: list[OrderRow]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool


SORT_KEYS = {
    "id": lambda row: row["id"],
    "amount": lambda row: row["amount"],
    "created_at": lambda row: row["created_at"],
}


def build_app(rows):
    app = FastAPI(title="订单列表")

    @app.get("/api/v1/orders", response_model=OrderPage)
    def list_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(5, ge=1, le=20),
        status: str | None = Query(None),
        q: str | None = Query(None, min_length=1, max_length=20),
        sort: str = Query("id"),
        order: str = Query("asc"),
    ):
        if sort not in SORT_KEYS:
            raise HTTPException(status_code=400, detail="sort 只支持 id、amount、created_at")
        if order not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="order 只支持 asc、desc")

        filtered = []
        for row in rows:
            if status and row["status"] != status:
                continue
            if q and q.lower() not in row["customer"].lower():
                continue
            filtered.append(row)

        filtered.sort(key=SORT_KEYS[sort], reverse=order == "desc")
        total = len(filtered)
        pages = math.ceil(total / page_size)
        start = (page - 1) * page_size
        return {
            "items": filtered[start : start + page_size],
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
        }

    return app


client = TestClient(build_app(orders))
print("列表接口已就绪，排序字段:", ", ".join(SORT_KEYS))


first = client.get("/api/v1/orders", params={"page": 1, "page_size": 5})
print("第一页:", first.status_code, {key: first.json()[key] for key in ("page", "page_size", "total", "pages", "has_next")})
print("编号:", [row["id"] for row in first.json()["items"]])

second = client.get("/api/v1/orders", params={"page": 2, "page_size": 5})
print("第二页编号:", [row["id"] for row in second.json()["items"]])

paid = client.get(
    "/api/v1/orders",
    params={"status": "paid", "sort": "amount", "order": "desc", "page_size": 3},
)
print("已支付按金额倒序:", [(row["id"], row["amount"]) for row in paid.json()["items"]])

search = client.get("/api/v1/orders", params={"q": "陈", "page_size": 10})
print("客户名含“陈”:", [(row["id"], row["customer"]) for row in search.json()["items"]])

beyond = client.get("/api/v1/orders", params={"page": 9, "page_size": 5})
print("超出页码:", beyond.status_code, beyond.json()["items"], beyond.json()["has_next"])

bad_sort = client.get("/api/v1/orders", params={"sort": "customer"})
print("非法排序:", bad_sort.status_code, bad_sort.json()["detail"])

bad_size = client.get("/api/v1/orders", params={"page_size": 100})
print("超出上限:", bad_size.status_code, bad_size.json()["detail"][0]["msg"])


rows = sorted(orders, key=lambda row: row["id"])
page_one = rows[:3]
page_two = rows[3:6]

extra = {
    "id": 1000,
    "customer": "新客户",
    "status": "pending",
    "amount": 10.0,
    "created_at": "2026-09-16",
}
shifted = sorted(rows + [extra], key=lambda row: row["id"])
shifted_page_two = shifted[3:6]

page_one_ids = [row["id"] for row in page_one]
overlap = sorted({row["id"] for row in shifted_page_two} & set(page_one_ids))

last_seen = page_one[-1]["id"]
cursor_page = [row for row in shifted if row["id"] > last_seen][:3]

print("offset 第一页:", page_one_ids)
print("原 offset 第二页:", [row["id"] for row in page_two])
print("插入新记录后 offset 第二页:", [row["id"] for row in shifted_page_two])
print("与第一页重复:", overlap)
print("cursor 第二页:", [row["id"] for row in cursor_page])
