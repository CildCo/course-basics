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

import itertools
import json
import math
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

BookStatus = Literal["available", "borrowed", "lost"]


class BookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=80)
    author: str = Field(min_length=1, max_length=40)
    year: int = Field(ge=1900, le=2100)
    status: BookStatus = "available"
    tags: list[str] = Field(default_factory=list, max_length=5)


class BookReplace(BookCreate):
    pass


class BookPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=80)
    author: str | None = Field(default=None, min_length=1, max_length=40)
    year: int | None = Field(default=None, ge=1900, le=2100)
    status: BookStatus | None = None
    tags: list[str] | None = Field(default=None, max_length=5)


class BookOut(BookCreate):
    id: int


class BookPage(BaseModel):
    items: list[BookOut]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool


book_rows = json.loads(data_path("books.json").read_text(encoding="utf-8"))
books = {row["id"]: row for row in book_rows}
book_ids = itertools.count(max(books) + 1)
print("初始图书:", len(books), "本")
print("借阅状态:", {
    status: sum(1 for row in books.values() if row["status"] == status)
    for status in ("available", "borrowed", "lost")
})


SORT_KEYS = {
    "id": lambda row: row["id"],
    "title": lambda row: row["title"],
    "year": lambda row: row["year"],
}
CODE_BY_STATUS = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    429: "rate_limited",
}


def request_id_of(request):
    return request.headers.get("X-Request-Id", "req-local")


def error_body(code, message, request_id, fields=None):
    payload = {"error": {"code": code, "message": message, "request_id": request_id}}
    if fields is not None:
        payload["error"]["fields"] = fields
    return payload


def build_app():
    app = FastAPI(title="图书 API")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request, exc):
        code = CODE_BY_STATUS.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, str(exc.detail), request_id_of(request)),
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
                request_id_of(request),
                fields=fields,
            ),
        )

    def find_book(book_id):
        book = books.get(book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="图书不存在")
        return book

    @app.get("/api/v1/books", response_model=BookPage)
    def list_books(
        page: int = Query(1, ge=1),
        page_size: int = Query(5, ge=1, le=20),
        status: BookStatus | None = Query(None),
        q: str | None = Query(None, min_length=1, max_length=30),
        sort: str = Query("id"),
        order: str = Query("asc"),
    ):
        if sort not in SORT_KEYS:
            raise HTTPException(status_code=400, detail="sort 只支持 id、title、year")
        if order not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="order 只支持 asc、desc")

        rows = []
        for row in books.values():
            if status is not None and row["status"] != status:
                continue
            if q is not None:
                keyword = q.lower()
                if keyword not in row["title"].lower() and keyword not in row["author"].lower():
                    continue
            rows.append(row)

        rows.sort(key=SORT_KEYS[sort], reverse=order == "desc")
        total = len(rows)
        pages = math.ceil(total / page_size)
        start = (page - 1) * page_size
        return {
            "items": rows[start : start + page_size],
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
        }

    @app.post("/api/v1/books", status_code=201)
    def create_book(payload: BookCreate):
        for row in books.values():
            if row["title"] == payload.title and row["author"] == payload.author:
                raise HTTPException(status_code=409, detail="同一作者的同名图书已存在")
        book = {"id": next(book_ids), **payload.model_dump()}
        books[book["id"]] = book
        return JSONResponse(
            status_code=201,
            content=BookOut(**book).model_dump(),
            headers={"Location": f"/api/v1/books/{book['id']}"},
        )

    @app.get("/api/v1/books/{book_id}", response_model=BookOut)
    def get_book(book_id: int):
        return find_book(book_id)

    @app.put("/api/v1/books/{book_id}", response_model=BookOut)
    def replace_book(book_id: int, payload: BookReplace):
        find_book(book_id)
        book = {"id": book_id, **payload.model_dump()}
        books[book_id] = book
        return book

    @app.patch("/api/v1/books/{book_id}", response_model=BookOut)
    def patch_book(book_id: int, payload: BookPatch):
        book = find_book(book_id)
        book.update(payload.model_dump(exclude_unset=True))
        return book

    @app.delete("/api/v1/books/{book_id}", status_code=204)
    def delete_book(book_id: int):
        find_book(book_id)
        del books[book_id]
        return Response(status_code=204)

    return app


client = TestClient(build_app())
endpoints = sorted(
    (method, route.path)
    for route in client.app.routes
    if route.path.startswith("/api/v1")
    for method in route.methods
)
print("端点数:", len(endpoints))
for method, path in endpoints:
    print(f"  {method:<7}{path}")


created = client.post(
    "/api/v1/books",
    json={"title": "API 设计手册", "author": "林一", "year": 2025, "tags": ["api", "design"]},
    headers={"X-Request-Id": "req-2001"},
)
book_id = created.json()["id"]
print("1 创建:", created.status_code, "id =", book_id, "Location =", created.headers["location"])

duplicate = client.post(
    "/api/v1/books",
    json={"title": "API 设计手册", "author": "林一", "year": 2026},
    headers={"X-Request-Id": "req-2002"},
)
print("2 重复创建:", duplicate.status_code, duplicate.json()["error"]["code"])

listing = client.get(
    "/api/v1/books",
    params={"status": "available", "sort": "year", "order": "desc", "page_size": 3},
)
print("3 列表:", listing.status_code, {key: listing.json()[key] for key in ("total", "pages", "has_next")})
print("   书名:", [row["title"] for row in listing.json()["items"]])

missing = client.get("/api/v1/books/9999", headers={"X-Request-Id": "req-2003"})
print("4 不存在:", missing.status_code, missing.json()["error"])

invalid = client.post(
    "/api/v1/books",
    json={"title": "", "author": "林一", "year": 1800, "color": "red"},
    headers={"X-Request-Id": "req-2004"},
)
print("5 校验失败:", invalid.status_code, [field["field"] for field in invalid.json()["error"]["fields"]])

patched = client.patch(f"/api/v1/books/{book_id}", json={"status": "borrowed"})
print("6 PATCH:", patched.status_code, patched.json()["status"], patched.json()["title"])

replaced = client.put(
    f"/api/v1/books/{book_id}",
    json={
        "title": "API 设计手册（第2版）",
        "author": "林一",
        "year": 2026,
        "status": "available",
        "tags": ["api"],
    },
)
print("7 PUT:", replaced.status_code, replaced.json()["title"], replaced.json()["year"], replaced.json()["tags"])

removed = client.delete(f"/api/v1/books/{book_id}")
print("8 DELETE:", removed.status_code, "body =", repr(removed.text))

gone = client.get(f"/api/v1/books/{book_id}")
print("9 删除后再查:", gone.status_code, gone.json()["error"]["code"])


checks = [
    ("创建返回 201", created.status_code == 201),
    ("创建带 Location", created.headers.get("location", "").startswith("/api/v1/books/")),
    ("重复返回 409", duplicate.status_code == 409),
    ("列表返回分页字段", {"items", "page", "page_size", "total", "pages", "has_next"} <= set(listing.json())),
    ("404 使用统一错误", missing.json()["error"]["code"] == "not_found"),
    ("422 有字段明细", len(invalid.json()["error"]["fields"]) == 3),
    ("PATCH 保留其他字段", patched.json()["title"] == "API 设计手册"),
    ("PUT 整体替换", replaced.json()["tags"] == ["api"]),
    ("DELETE 无正文", removed.status_code == 204 and removed.text == ""),
]

for name, passed in checks:
    print("通过" if passed else "失败", name)

contract = {
    "version": "v1",
    "base_path": "/api/v1",
    "resources": ["books"],
    "pagination": {"page": 1, "page_size": 5, "max_page_size": 20},
    "errors": {"404": "not_found", "409": "conflict", "422": "validation_error"},
    "endpoints": [
        "GET /books",
        "POST /books",
        "GET /books/{id}",
        "PUT /books/{id}",
        "PATCH /books/{id}",
        "DELETE /books/{id}",
    ],
}
target = output_dir() / "api-contract.json"
target.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("断言通过:", sum(1 for _, passed in checks if passed), "/", len(checks))
print("契约文件:", target.name)
